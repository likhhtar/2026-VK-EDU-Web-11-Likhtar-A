import os
import random
import uuid
from typing import Iterator, List, Optional, Tuple

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Min
from faker import Faker

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag

fake = Faker()
Faker.seed(42)
random.seed(42)

LIKES_PER_RATIO = 200
USER_BATCH = 2_000
QUESTION_BATCH = 5_000
ANSWER_BATCH = 10_000
TAGS_THROUGH_BATCH = 50_000
LIKES_BATCH = 50_000
PROFILE_BATCH = 5_000


def _iter_limited_cartesian(
    uids: List[int],
    entity_ids: List[int],
    target: int,
) -> Iterator[Tuple[int, int]]:
    n_u, n_e = len(uids), len(entity_ids)
    capacity = n_u * n_e
    if target < 0 or target > capacity:
        raise ValueError('target out of range')
    count = 0
    u_idx, e_idx = 0, 0
    while count < target:
        yield uids[u_idx], entity_ids[e_idx]
        count += 1
        e_idx += 1
        if e_idx >= n_e:
            e_idx = 0
            u_idx += 1


def _env_int(name: str) -> Optional[int]:
    v = os.environ.get(name, '').strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError as exc:
        raise CommandError(f'{name} должен быть целым числом') from exc


class Command(BaseCommand):
    help = (
        'Наполняет базу тестовыми данными. Добавляет: ratio пользователей, ratio*10 вопросов, '
        'ratio*100 ответов, ratio тегов, лайки вопросов и ответов (до FILLDB_LIKES_PER_RATIO*ratio, '
        'с ограничением уникальными парами).'
    )

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int, help='Коэффициент наполнения')

    def handle(self, *args, **options):
        ratio = options['ratio']
        if ratio < 1:
            raise CommandError('ratio должен быть >= 1')

        likes_per_ratio = _env_int('FILLDB_LIKES_PER_RATIO') or LIKES_PER_RATIO

        run = uuid.uuid4().hex[:10]
        self.stdout.write(self.style.NOTICE(f'run_id={run}, ratio={ratio}, likes_per_ratio={likes_per_ratio}'))

        n_users = ratio
        n_questions = ratio * 10
        n_answers = ratio * 100
        n_tags = ratio
        requested_ql = ratio * likes_per_ratio
        requested_al = ratio * likes_per_ratio

        user_ids: List[int] = []
        question_ids: List[int] = []
        answer_ids: List[int] = []
        tag_ids: List[int] = []

        user_ids = self._bulk_users(n_users, run)
        if len(user_ids) != n_users:
            raise CommandError('не удалось создать ожидаемое количество пользователей')

        self._bulk_profiles_batched(user_ids)
        tag_ids = self._bulk_tags(n_tags, run)
        if len(tag_ids) != n_tags:
            raise CommandError('не удалось создать ожидаемое количество тегов')

        question_ids = self._bulk_questions_batched(n_questions, user_ids, batch_size=QUESTION_BATCH)
        if len(question_ids) != n_questions:
            raise CommandError('не удалось создать ожидаемое количество вопросов')

        if tag_ids and question_ids:
            self._bulk_question_tags_batched(question_ids, tag_ids)

        self._bulk_answers_batched(
            n_answers,
            question_ids=question_ids,
            user_ids=user_ids,
            batch_size=ANSWER_BATCH,
            answer_ids_out=answer_ids,
        )
        if n_answers and len(answer_ids) != n_answers:
            raise CommandError('не удалось создать ожидаемое количество ответов')

        if answer_ids and question_ids:
            self._apply_single_accepted_per_question(answer_ids, question_ids)

        max_ql = len(user_ids) * len(question_ids)
        max_al = len(user_ids) * len(answer_ids)

        target_ql = min(requested_ql, max_ql)
        target_al = min(requested_al, max_al)

        if requested_ql > max_ql and max_ql == 0:
            raise CommandError(
                f'нельзя создать лайки вопросов: пользователей={len(user_ids)}, вопросов={len(question_ids)}'
            )
        if requested_ql > max_ql:
            self.stdout.write(
                self.style.WARNING(
                    f'Лайки вопросов: запрошено {requested_ql}, максимум уникальных пар {max_ql} — '
                    f'создаём {target_ql} (уменьшите ratio или FILLDB_LIKES_PER_RATIO, либо это ожидаемо).'
                )
            )
        if requested_al > max_al and max_al > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'Лайки ответов: запрошено {requested_al}, максимум уникальных пар {max_al} — '
                    f'создаём {target_al}.'
                )
            )
        if max_al == 0 and requested_al > 0:
            self.stdout.write(
                self.style.WARNING('Лайки ответов: отсутствуют ответы — пропуск.')
            )

        if target_ql and user_ids and question_ids:
            self._bulk_likes_batched(
                model=QuestionLike,
                uids=user_ids,
                eids=question_ids,
                target=target_ql,
                user_field='user_id',
                entity_field='question_id',
            )
        if target_al and user_ids and answer_ids:
            self._bulk_likes_batched(
                model=AnswerLike,
                uids=user_ids,
                eids=answer_ids,
                target=target_al,
                user_field='user_id',
                entity_field='answer_id',
            )

        self.stdout.write(self.style.SUCCESS('Готово.'))

    def _bulk_users(self, n: int, run: str) -> List[int]:
        """Создаёт пользователей батчами, коммит по батчам; в памяти — только id."""
        out: List[int] = []
        chunk: List[User] = []
        pwd = make_password('pass')
        for i in range(n):
            chunk.append(
                User(
                    username=f'u_{run}_{i}',
                    email=f'u_{run}_{i}@example.com',
                    password=pwd,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                )
            )
            if len(chunk) >= USER_BATCH:
                with transaction.atomic():
                    User.objects.bulk_create(chunk, batch_size=USER_BATCH)
                out.extend(self._pks_for_users(chunk))
                self.stdout.write(f'users +{len(chunk)} ({len(out)}/{n})')
                chunk = []
        if chunk:
            with transaction.atomic():
                User.objects.bulk_create(chunk, batch_size=USER_BATCH)
            out.extend(self._pks_for_users(chunk))
        return out

    @staticmethod
    def _pks_for_users(row: List[User]) -> List[int]:
        return [u.pk for u in row if u.pk]

    def _bulk_profiles_batched(self, user_ids: List[int]) -> None:
        for i in range(0, len(user_ids), PROFILE_BATCH):
            part = user_ids[i : i + PROFILE_BATCH]
            profs = [Profile(user_id=uid, rating=random.randint(1, 5000)) for uid in part]
            with transaction.atomic():
                Profile.objects.bulk_create(profs, batch_size=PROFILE_BATCH)

    def _bulk_tags(self, n: int, run: str) -> List[int]:
        tags = [Tag(name=f't{run}{i}', color=fake.hex_color()) for i in range(n)]
        with transaction.atomic():
            Tag.objects.bulk_create(tags, batch_size=2000)
        return [t.pk for t in tags if t.pk]

    def _bulk_questions_batched(
        self,
        questions_count: int,
        user_ids: List[int],
        *,
        batch_size: int,
    ) -> List[int]:
        if not user_ids or questions_count == 0:
            return []
        out: List[int] = []
        chunk: List[Question] = []
        for i in range(questions_count):
            chunk.append(
                Question(
                    title=fake.sentence(nb_words=6)[:255],
                    text='\n\n'.join(fake.paragraphs(nb=3)),
                    code_snippet='' if random.random() > 0.2 else fake.paragraph(nb_sentences=2),
                    author_id=random.choice(user_ids),
                    views=random.randint(0, 10_000),
                )
            )
            if len(chunk) >= batch_size:
                with transaction.atomic():
                    Question.objects.bulk_create(chunk, batch_size=batch_size)
                out.extend(self._pks_for_questions(chunk))
                self.stdout.write(f'questions +{len(chunk)} ({len(out)}/{questions_count})')
                chunk = []
        if chunk:
            with transaction.atomic():
                Question.objects.bulk_create(chunk, batch_size=batch_size)
            out.extend(self._pks_for_questions(chunk))
        return out

    @staticmethod
    def _pks_for_questions(row: List[Question]) -> List[int]:
        return [q.pk for q in row if q.pk]

    def _bulk_question_tags_batched(self, question_ids: List[int], tag_ids: List[int]) -> None:
        Through = Question.tags.through
        if not tag_ids:
            return
        rows: List = []
        for qid in question_ids:
            k = random.randint(1, min(3, len(tag_ids)))
            for tid in random.sample(tag_ids, k=k):
                rows.append(Through(question_id=qid, tag_id=tid))
                if len(rows) >= TAGS_THROUGH_BATCH:
                    with transaction.atomic():
                        Through.objects.bulk_create(rows, batch_size=TAGS_THROUGH_BATCH)
                    rows = []
        if rows:
            with transaction.atomic():
                Through.objects.bulk_create(rows, batch_size=TAGS_THROUGH_BATCH)

    def _bulk_answers_batched(
        self,
        n: int,
        *,
        question_ids: List[int],
        user_ids: List[int],
        batch_size: int,
        answer_ids_out: List[int],
    ) -> None:
        if n == 0 or not question_ids or not user_ids:
            return
        chunk: List[Answer] = []
        for _ in range(n):
            chunk.append(
                Answer(
                    question_id=random.choice(question_ids),
                    author_id=random.choice(user_ids),
                    text='\n\n'.join(fake.paragraphs(nb=2)),
                    is_accepted=False,
                )
            )
            if len(chunk) >= batch_size:
                with transaction.atomic():
                    Answer.objects.bulk_create(chunk, batch_size=batch_size)
                answer_ids_out.extend(self._pks_for_answers(chunk))
                self.stdout.write(f'answers +{len(chunk)} ({len(answer_ids_out)}/{n})')
                chunk = []
        if chunk:
            with transaction.atomic():
                Answer.objects.bulk_create(chunk, batch_size=batch_size)
            answer_ids_out.extend(self._pks_for_answers(chunk))

    @staticmethod
    def _pks_for_answers(row: List[Answer]) -> List[int]:
        return [a.pk for a in row if a.pk]

    def _apply_single_accepted_per_question(
        self,
        _answer_ids: List[int],
        question_ids: List[int],
    ) -> None:
        if not question_ids:
            return
        with transaction.atomic():
            per_q = (
                Answer.objects.filter(question_id__in=question_ids, is_accepted=False)
                .values('question_id')
                .annotate(keep=Min('id'))
            )
            rows: List[dict] = list(per_q)
        if not rows:
            return
        sample = max(1, int(0.05 * len(rows)))
        random.shuffle(rows)
        to_accept = [r['keep'] for r in rows[:sample]]
        with transaction.atomic():
            Answer.objects.filter(pk__in=to_accept).update(is_accepted=True)

    def _bulk_likes_batched(
        self,
        *,
        model,
        uids: List[int],
        eids: List[int],
        target: int,
        user_field: str,
        entity_field: str,
    ) -> None:
        if target <= 0 or not uids or not eids:
            return
        n_u, n_e = len(uids), len(eids)
        capacity = n_u * n_e
        if target > capacity:
            raise CommandError(
                f'нельзя создать {target} уникальных лайков: ёмкость пар {n_u}×{n_e} = {capacity}'
            )
        batch: List = []
        for u, e in _iter_limited_cartesian(uids, eids, target):
            batch.append(model(**{user_field: u, entity_field: e}))
            if len(batch) >= LIKES_BATCH:
                with transaction.atomic():
                    model.objects.bulk_create(batch, batch_size=LIKES_BATCH)
                batch = []
        if batch:
            with transaction.atomic():
                model.objects.bulk_create(batch, batch_size=LIKES_BATCH)