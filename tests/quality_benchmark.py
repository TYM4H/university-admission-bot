import argparse
import asyncio
import json
import re
import time
from dataclasses import dataclass, field

from app.services.chat_service import chat_service


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    suite: str
    question: str
    required_any_groups: tuple[tuple[str, ...], ...] = ()
    optional_any_groups: tuple[tuple[str, ...], ...] = ()
    forbidden_any: tuple[str, ...] = ()
    min_optional_for_ok: int = 0


@dataclass
class CaseResult:
    name: str
    question: str
    verdict: str
    latency_sec: float
    answer: str
    matched_required: int
    total_required: int
    matched_optional: int
    total_optional: int
    forbidden_hits: list[str] = field(default_factory=list)
    missing_required: list[tuple[str, ...]] = field(default_factory=list)


CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        name="greeting",
        suite="basic",
        question="привет",
        required_any_groups=(
            ("привет", "здравствуйте", "добрый"),
            ("вопрос", "поступлен"),
        ),
        forbidden_any=("поехали",),
    ),
    BenchmarkCase(
        name="required_documents",
        suite="basic",
        question="Какие документы нужны для поступления?",
        required_any_groups=(
            ("документ подтверждающий личность", "документ, подтверждающий личность"),
            ("документ об образовании",),
        ),
        optional_any_groups=(
            ("персонифицирован", "снилс"),
            ("индивидуальн",),
            ("льгот",),
        ),
        min_optional_for_ok=1,
    ),
    BenchmarkCase(
        name="submission_start_date",
        suite="basic",
        question="С какого числа можно подавать документы?",
        required_any_groups=(("20 июня",),),
    ),
    BenchmarkCase(
        name="submission_methods",
        suite="basic",
        question="Как можно подать документы для поступления?",
        required_any_groups=(
            ("госуслуг",),
            ("лично", "приёмной комиссии", "приемной комиссии"),
        ),
    ),
    BenchmarkCase(
        name="max_programs",
        suite="basic",
        question="На сколько направлений можно подать документы?",
        required_any_groups=(
            ("5 направлен", "не более чем на 5"),
            ("магистратур", "аспирантур"),
        ),
    ),
    BenchmarkCase(
        name="consent_deadline_bachelor",
        suite="basic",
        question="До какого числа нужно подать согласие о зачислении на бакалавриат?",
        required_any_groups=(("5 августа",),),
        optional_any_groups=(("12:00",),),
        min_optional_for_ok=1,
    ),
    BenchmarkCase(
        name="admissions_office_address",
        suite="basic",
        question="По какому адресу находится приёмная комиссия МТУСИ?",
        required_any_groups=(
            ("авиамоторн",),
            ("стр.39", "стр 39", "39"),
        ),
    ),
    BenchmarkCase(
        name="budget_and_paid",
        suite="basic",
        question="Можно ли одновременно подать документы на бюджет и платное?",
        required_any_groups=(("да", "можно"),),
    ),
    BenchmarkCase(
        name="notary_copies",
        suite="basic",
        question="Нужно ли заверять копии документов у нотариуса?",
        required_any_groups=(("не требуется", "нет, не требуется", "не нужно"),),
    ),
    BenchmarkCase(
        name="medical_form_086",
        suite="basic",
        question="Нужна ли при подаче документов справка 086/у?",
        required_any_groups=(("не требуется", "не нужна", "не требуется при подаче"),),
    ),
    BenchmarkCase(
        name="ege_validity",
        suite="basic",
        question="Сколько лет действуют результаты ЕГЭ?",
        required_any_groups=(
            ("4 лет", "четыр",),
            ("следующ", "за годом сдачи"),
        ),
    ),
    BenchmarkCase(
        name="parents_consent",
        suite="basic",
        question="Могут ли родители подать или забрать согласие о зачислении?",
        required_any_groups=(
            ("да",),
            ("доверен",),
        ),
        optional_any_groups=(("удостоверяющ", "документ удостоверяющий личность"),),
        min_optional_for_ok=1,
    ),
    BenchmarkCase(
        name="army_deferral",
        suite="basic",
        question="Есть ли отсрочка от армии?",
        required_any_groups=(
            ("отсрочк",),
            ("очн",),
        ),
    ),
    BenchmarkCase(
        name="hostel_full_time",
        suite="basic",
        question="Есть ли общежитие для очной формы обучения?",
        required_any_groups=(
            ("270",),
            ("60 км", "мкад"),
        ),
    ),
    BenchmarkCase(
        name="hostel_part_time",
        suite="basic",
        question="Есть ли общежитие для заочной формы обучения?",
        required_any_groups=(("не предостав",),),
    ),
    BenchmarkCase(
        name="offtopic_weather",
        suite="basic",
        question="Какая сегодня погода в Москве?",
        required_any_groups=(("только по вопросам приёмной комиссии", "только по вопросам приемной комиссии", "помогаю только по вопросам приёмной комиссии", "помогаю только по вопросам приемной комиссии"),),
        forbidden_any=("градус", "дожд", "снег", "солнеч", "пасмур", "ветер"),
    ),
    BenchmarkCase(
        name="slang_submission_methods",
        suite="hard",
        question="Че как документы то к вам подать?",
        required_any_groups=(
            ("госуслуг",),
            ("лично", "приемной комиссии", "приёмной комиссии"),
        ),
    ),
    BenchmarkCase(
        name="slang_documents",
        suite="hard",
        question="Что по докам для поступления надо вообще?",
        required_any_groups=(
            ("личность",),
            ("образован",),
        ),
        optional_any_groups=(
            ("снилс", "персонифицирован"),
            ("индивидуальн",),
            ("льгот",),
        ),
        min_optional_for_ok=1,
    ),
    BenchmarkCase(
        name="ambiguous_hostel",
        suite="hard",
        question="Есть ли общага?",
        required_any_groups=(
            ("очная", "очно", "очной формы"),
            ("заочн", "очно-заочн"),
        ),
        optional_any_groups=(
            ("270",),
            ("60 км", "мкад"),
        ),
        min_optional_for_ok=1,
    ),
    BenchmarkCase(
        name="after_college_exams",
        suite="hard",
        question="Я после колледжа, могу сдавать внутренние вступительные?",
        required_any_groups=(
            ("после колледжа",),
            ("родствен", "то же направление", "тоже направление"),
        ),
    ),
    BenchmarkCase(
        name="combine_ege_and_internal",
        suite="hard",
        question="Если у меня и ЕГЭ есть, и внутренние могу сдавать, можно комбинировать результаты?",
        required_any_groups=(
            ("да",),
            ("любой успешный результат", "выбрать любой успешный результат", "право выбрать"),
        ),
    ),
    BenchmarkCase(
        name="change_program_deadline",
        suite="hard",
        question="До какого числа можно передумать и поменять направление?",
        required_any_groups=(
            ("20 июля", "25 июля"),
            ("8 августа", "15 августа"),
        ),
    ),
    BenchmarkCase(
        name="commercial_contract_minor",
        suite="hard",
        question="Мне нет 18, я могу заключить договор на платное?",
        required_any_groups=(
            ("родител", "законн"),
        ),
    ),
    BenchmarkCase(
        name="offtopic_scholarship",
        suite="hard",
        question="Какая у вас стипендия у студентов?",
        required_any_groups=(
            ("только по вопросам приёмной комиссии", "только по вопросам приемной комиссии", "помогаю только по вопросам приёмной комиссии", "помогаю только по вопросам приемной комиссии"),
        ),
        forbidden_any=("руб", "стипенд", "выплат"),
    ),
    BenchmarkCase(
        name="offtopic_programming",
        suite="hard",
        question="Напиши код на Python для телеграм-бота",
        required_any_groups=(
            ("только по вопросам приёмной комиссии", "только по вопросам приемной комиссии", "помогаю только по вопросам приёмной комиссии", "помогаю только по вопросам приемной комиссии"),
        ),
        forbidden_any=("def ", "python", "import ", "aiogram"),
    ),
]


def normalize_text(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def group_matches(answer: str, group: tuple[str, ...]) -> bool:
    return any(normalize_text(phrase) in answer for phrase in group)


def evaluate_case(case: BenchmarkCase, answer: str, latency_sec: float) -> CaseResult:
    normalized_answer = normalize_text(answer)
    forbidden_hits = [
        phrase for phrase in case.forbidden_any if normalize_text(phrase) in normalized_answer
    ]

    missing_required = [
        group for group in case.required_any_groups if not group_matches(normalized_answer, group)
    ]
    matched_required = len(case.required_any_groups) - len(missing_required)

    matched_optional = sum(
        1 for group in case.optional_any_groups if group_matches(normalized_answer, group)
    )

    if forbidden_hits:
        verdict = "wrong"
    elif case.required_any_groups and matched_required == len(case.required_any_groups):
        verdict = "ok" if matched_optional >= case.min_optional_for_ok else "partial"
    elif matched_required > 0:
        verdict = "partial"
    else:
        verdict = "wrong"

    return CaseResult(
        name=case.name,
        question=case.question,
        verdict=verdict,
        latency_sec=latency_sec,
        answer=answer,
        matched_required=matched_required,
        total_required=len(case.required_any_groups),
        matched_optional=matched_optional,
        total_optional=len(case.optional_any_groups),
        forbidden_hits=forbidden_hits,
        missing_required=missing_required,
    )


async def run_benchmark(limit: int | None, suite: str) -> list[CaseResult]:
    selected_cases = [case for case in CASES if suite == "all" or case.suite == suite]
    if limit is not None:
        selected_cases = selected_cases[:limit]
    base_user_id = int(time.time())
    results: list[CaseResult] = []

    for index, case in enumerate(selected_cases, start=1):
        user_id = base_user_id + index
        started_at = time.perf_counter()
        try:
            answer = await chat_service.get_response(user_id=user_id, text=case.question)
        except Exception as exc:
            latency_sec = time.perf_counter() - started_at
            results.append(
                CaseResult(
                    name=case.name,
                    question=case.question,
                    verdict="wrong",
                    latency_sec=latency_sec,
                    answer=f"ERROR: {exc!r}",
                    matched_required=0,
                    total_required=len(case.required_any_groups),
                    matched_optional=0,
                    total_optional=len(case.optional_any_groups),
                )
            )
            continue

        latency_sec = time.perf_counter() - started_at
        results.append(evaluate_case(case, answer, latency_sec))

    return results


def print_summary(results: list[CaseResult]) -> None:
    ok_count = sum(result.verdict == "ok" for result in results)
    partial_count = sum(result.verdict == "partial" for result in results)
    wrong_count = sum(result.verdict == "wrong" for result in results)
    avg_latency = sum(result.latency_sec for result in results) / len(results)

    print(
        f"Summary: ok={ok_count} partial={partial_count} wrong={wrong_count} "
        f"avg_latency={avg_latency:.2f}s total={len(results)}"
    )
    print()

    for result in results:
        print(
            f"[{result.verdict.upper():7}] {result.name:24} {result.latency_sec:6.2f}s | "
            f"{result.question}"
        )
        if result.forbidden_hits:
            print(f"  forbidden: {', '.join(result.forbidden_hits)}")
        if result.missing_required:
            missing = [" / ".join(group) for group in result.missing_required]
            print(f"  missing: {missing}")
        print(f"  answer: {result.answer}")
        print()


def build_json_payload(results: list[CaseResult]) -> list[dict]:
    return [
        {
            "name": result.name,
            "question": result.question,
            "verdict": result.verdict,
            "latency_sec": round(result.latency_sec, 3),
            "matched_required": result.matched_required,
            "total_required": result.total_required,
            "matched_optional": result.matched_optional,
            "total_optional": result.total_optional,
            "forbidden_hits": result.forbidden_hits,
            "missing_required": [list(group) for group in result.missing_required],
            "answer": result.answer,
        }
        for result in results
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run end-to-end answer quality benchmark.")
    parser.add_argument(
        "--suite",
        choices=("basic", "hard", "all"),
        default="basic",
        help="Benchmark suite to run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Run only the first N benchmark cases.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print results as JSON instead of the text summary.",
    )
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()
    results = await run_benchmark(args.limit, args.suite)

    if args.json:
        print(json.dumps(build_json_payload(results), ensure_ascii=False, indent=2))
    else:
        print_summary(results)

    return 1 if any(result.verdict == "wrong" for result in results) else 0


def main() -> None:
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
