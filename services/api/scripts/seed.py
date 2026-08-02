#!/usr/bin/env python3
"""Seed database with demo data: 1 attorney, 1 paralegal, 1 inmate, 1 admin, 1 demo case shared to all but admin."""
import asyncio
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import async_session
from app.models.case import Case
from app.models.opinion import Opinion
from app.models.share import Share
from app.models.user import User

# Small, verified starter set of well-known U.S. Supreme Court precedents for
# the /similar full-text search feature. These are real cases with real
# citations and holdings (not fabricated case law) — deliberately chosen over
# invented sample data since this is legal-aid software used by incarcerated
# users, where a fake citation could cause real harm. This set is meant to be
# superseded by a real ingestion/RAG pipeline (Should-Have roadmap item), not
# to be a comprehensive precedent library. Jurisdiction is "US" for all
# entries (all are SCOTUS cases) — no PA/state entries are included because
# none were verified with confidence; don't force-fit values just to cover
# every filter option in the UI.
PRECEDENT_OPINIONS = [
    {
        "title": "Gideon v. Wainwright",
        "citation": "372 U.S. 335 (1963)",
        "jurisdiction": "US",
        "disposition": "REVERSED",
        "date_decided": date(1963, 3, 18),
        "source": "https://supreme.justia.com/cases/federal/us/372/335/",
        "headline": (
            "The Sixth Amendment right to counsel is a fundamental right that applies to "
            "state felony prosecutions through the Fourteenth Amendment; an indigent "
            "defendant charged with a felony has a right to an appointed lawyer."
        ),
        "content": (
            "Clarence Earl Gideon was charged with a felony in Florida state court and "
            "could not afford to hire an attorney. The trial court denied his request for "
            "appointed counsel because Florida law only provided court-appointed counsel "
            "in capital cases. Gideon was convicted and later filed a petition for a writ "
            "of habeas corpus, arguing that the denial of counsel violated his right to a "
            "fair trial. On habeas corpus appeal the United States Supreme Court held that "
            "the right to counsel guaranteed by the Sixth Amendment is a fundamental right "
            "essential to a fair trial and is made obligatory on the states by the "
            "Fourteenth Amendment's due process clause. The Court reversed and remanded, "
            "ruling that any person too poor to hire a lawyer must be furnished counsel by "
            "the state in a felony case. This decision established the right to appointed "
            "counsel that underlies later ineffective assistance of counsel claims and "
            "remains a cornerstone of habeas corpus appeals raising denial-of-counsel issues."
        ),
    },
    {
        "title": "Strickland v. Washington",
        "citation": "466 U.S. 668 (1984)",
        "jurisdiction": "US",
        "disposition": "REVERSED",
        "date_decided": date(1984, 5, 14),
        "source": "https://supreme.justia.com/cases/federal/us/466/668/",
        "headline": (
            "To prevail on an ineffective assistance of counsel claim, a defendant must "
            "show both that counsel's performance was deficient and that the deficient "
            "performance prejudiced the defense — the two-prong Strickland test."
        ),
        "content": (
            "David Washington pleaded guilty to capital murder charges and, after an "
            "unfavorable sentencing outcome, argued on habeas corpus appeal that his trial "
            "counsel provided ineffective assistance of counsel by failing to investigate "
            "and present mitigating evidence at sentencing. The Court of Appeals agreed and "
            "granted habeas relief. The Supreme Court reversed, establishing a two-part test "
            "for ineffective assistance of counsel claims under the Sixth Amendment: a "
            "defendant must show that counsel's performance fell below an objective "
            "standard of reasonableness, and that there is a reasonable probability that, "
            "but for counsel's errors, the result of the proceeding would have been "
            "different. Applying this standard, the Court held that Washington's counsel's "
            "strategic decisions did not constitute ineffective assistance and reinstated "
            "the denial of habeas relief. Strickland remains the controlling standard for "
            "evaluating ineffective assistance of counsel claims in criminal appeals and "
            "sentencing challenges."
        ),
    },
    {
        "title": "Miranda v. Arizona",
        "citation": "384 U.S. 436 (1966)",
        "jurisdiction": "US",
        "disposition": "REVERSED",
        "date_decided": date(1966, 6, 13),
        "source": "https://supreme.justia.com/cases/federal/us/384/436/",
        "headline": (
            "Prior to any custodial interrogation, police must warn a suspect of the right "
            "to remain silent, that anything said may be used against them, and the right "
            "to an attorney, including appointed counsel if indigent."
        ),
        "content": (
            "Ernesto Miranda was arrested and interrogated by police without being informed "
            "of his constitutional rights, and he signed a written confession that was used "
            "to convict him at trial. On appeal, the Supreme Court reversed the conviction, "
            "holding that statements obtained during custodial interrogation are "
            "inadmissible unless the prosecution demonstrates the use of procedural "
            "safeguards effective to secure the privilege against self-incrimination, "
            "including a warning of the right to remain silent, that anything said can be "
            "used against the person, and the right to the presence of an attorney, "
            "retained or appointed. These Miranda warnings are now a standard part of "
            "criminal procedure and are frequently raised in habeas corpus appeals "
            "challenging the admissibility of confessions and the effectiveness of counsel "
            "during interrogation."
        ),
    },
    {
        "title": "Brady v. Maryland",
        "citation": "373 U.S. 83 (1963)",
        "jurisdiction": "US",
        "disposition": "AFFIRMED",
        "date_decided": date(1963, 5, 13),
        "source": "https://supreme.justia.com/cases/federal/us/373/83/",
        "headline": (
            "The prosecution's suppression of evidence favorable to a defendant who has "
            "requested it violates due process where the evidence is material to guilt or "
            "punishment, regardless of the good faith of the prosecution."
        ),
        "content": (
            "John Brady and a companion were convicted of murder. Before trial, Brady's "
            "counsel requested the prosecution turn over the companion's extrajudicial "
            "statements, but the prosecution withheld a statement in which the companion "
            "admitted to the actual killing. The Maryland Court of Appeals held that "
            "suppression of this evidence violated due process but limited the remedy to a "
            "new trial on the question of punishment, since Brady's own admissions "
            "supported the finding of guilt. The Supreme Court affirmed, holding that "
            "suppression by the prosecution of evidence favorable to an accused upon "
            "request violates due process where the evidence is material either to guilt or "
            "to punishment, irrespective of the good faith or bad faith of the prosecution. "
            "This disclosure obligation, now known as the Brady rule, is a frequent basis "
            "for post-conviction appeals alleging missing documents and filing "
            "inconsistencies by the prosecution."
        ),
    },
    {
        "title": "Batson v. Kentucky",
        "citation": "476 U.S. 79 (1986)",
        "jurisdiction": "US",
        "disposition": "REVERSED",
        "date_decided": date(1986, 4, 30),
        "source": "https://supreme.justia.com/cases/federal/us/476/79/",
        "headline": (
            "The Equal Protection Clause forbids a prosecutor from using peremptory jury "
            "strikes to exclude potential jurors solely on account of their race."
        ),
        "content": (
            "James Batson, a Black defendant, was tried by an all-white jury after the "
            "prosecutor used peremptory strikes to remove all Black members of the jury "
            "venire. The Supreme Court reversed the conviction and held that the Equal "
            "Protection Clause prohibits a prosecutor from using peremptory challenges to "
            "exclude jurors solely on the basis of race, and established a three-step "
            "framework for defendants to raise and prove such claims. The case was remanded "
            "for further proceedings consistent with this framework. Batson claims are "
            "commonly raised on direct appeal and in post-conviction proceedings "
            "challenging jury selection procedures."
        ),
    },
    {
        "title": "Escobedo v. Illinois",
        "citation": "378 U.S. 478 (1964)",
        "jurisdiction": "US",
        "disposition": "REVERSED",
        "date_decided": date(1964, 6, 22),
        "source": "https://supreme.justia.com/cases/federal/us/378/478/",
        "headline": (
            "A suspect has a right to counsel once police interrogation shifts from "
            "investigatory to accusatory and the suspect has requested and been denied "
            "access to an attorney."
        ),
        "content": (
            "Danny Escobedo was interrogated by police and repeatedly asked to speak with "
            "his attorney, who was present at the police station but was not permitted to "
            "see his client. Escobedo made incriminating statements without the assistance "
            "of counsel and was convicted of murder. The Supreme Court reversed the "
            "conviction, holding that where police interrogation shifts from a general "
            "investigation to focus on a particular suspect who has been taken into "
            "custody, and the suspect has requested and been denied an opportunity to "
            "consult with his attorney, the accused has been denied the assistance of "
            "counsel in violation of the Sixth Amendment, and any statement elicited is "
            "inadmissible. Escobedo is frequently cited alongside Miranda in appeals "
            "challenging the admissibility of confessions obtained during custodial "
            "interrogation."
        ),
    },
    {
        "title": "Terry v. Ohio",
        "citation": "392 U.S. 1 (1968)",
        "jurisdiction": "US",
        "disposition": "AFFIRMED",
        "date_decided": date(1968, 6, 10),
        "source": "https://supreme.justia.com/cases/federal/us/392/1/",
        "headline": (
            "Police may briefly stop and frisk a person for weapons without a warrant or "
            "probable cause if the officer has reasonable, articulable suspicion that the "
            "person is involved in criminal activity and may be armed."
        ),
        "content": (
            "A police officer observed John Terry and two companions behaving in a manner "
            "suggesting they were casing a store for a robbery. The officer stopped the men "
            "and patted down their outer clothing, discovering a concealed weapon on Terry, "
            "who was convicted of carrying a concealed weapon. The Supreme Court affirmed "
            "the conviction, holding that a police officer may conduct a brief "
            "investigatory stop and a protective frisk for weapons without a warrant or "
            "probable cause, so long as the officer has reasonable, articulable suspicion "
            "that criminal activity is afoot and that the person may be armed and "
            "dangerous. This reasonable suspicion standard governs the constitutionality of "
            "stop-and-frisk searches raised in suppression motions and appeals."
        ),
    },
    {
        "title": "Mapp v. Ohio",
        "citation": "367 U.S. 643 (1961)",
        "jurisdiction": "US",
        "disposition": "REVERSED",
        "date_decided": date(1961, 6, 19),
        "source": "https://supreme.justia.com/cases/federal/us/367/643/",
        "headline": (
            "The Fourth Amendment exclusionary rule, barring the use of illegally seized "
            "evidence in criminal prosecutions, applies to the states through the "
            "Fourteenth Amendment."
        ),
        "content": (
            "Police searched Dollree Mapp's home without a valid search warrant and found "
            "allegedly obscene materials, which were used to convict her at trial. The "
            "Supreme Court reversed the conviction, holding that the exclusionary rule, "
            "which bars the admission of evidence obtained in violation of the Fourth "
            "Amendment, applies to state criminal prosecutions through the Fourteenth "
            "Amendment's due process clause. Evidence obtained through an unreasonable "
            "search and seizure is inadmissible in both federal and state courts. Mapp "
            "remains a foundational citation in appeals and suppression motions challenging "
            "evidence obtained without a valid warrant."
        ),
    },
    {
        "title": "Apprendi v. New Jersey",
        "citation": "530 U.S. 466 (2000)",
        "jurisdiction": "US",
        "disposition": "REVERSED",
        "date_decided": date(2000, 6, 26),
        "source": "https://supreme.justia.com/cases/federal/us/530/466/",
        "headline": (
            "Other than the fact of a prior conviction, any fact that increases the penalty "
            "for a crime beyond the prescribed statutory maximum must be submitted to a "
            "jury and proved beyond a reasonable doubt."
        ),
        "content": (
            "Charles Apprendi fired shots into a neighbor's home and pleaded guilty to a "
            "firearms offense carrying a statutory maximum sentence. A New Jersey "
            "hate-crime statute allowed a judge, applying a preponderance-of-the-evidence "
            "standard, to impose an extended sentence beyond that maximum upon finding the "
            "crime was committed with a biased purpose. The Supreme Court reversed the "
            "extended sentence, holding that other than the fact of a prior conviction, any "
            "fact that increases the penalty for a crime beyond the prescribed statutory "
            "maximum must be submitted to a jury and proved beyond a reasonable doubt. "
            "Apprendi is a leading citation in sentencing modification appeals challenging "
            "judicial fact-finding that increases a defendant's sentence."
        ),
    },
    {
        "title": "Graham v. Florida",
        "citation": "560 U.S. 48 (2010)",
        "jurisdiction": "US",
        "disposition": "REVERSED",
        "date_decided": date(2010, 5, 17),
        "source": "https://supreme.justia.com/cases/federal/us/560/48/",
        "headline": (
            "The Eighth Amendment prohibits sentencing a juvenile offender to life in "
            "prison without the possibility of parole for a non-homicide crime; the state "
            "must provide a meaningful opportunity for release based on demonstrated "
            "maturity and rehabilitation."
        ),
        "content": (
            "Terrance Graham committed armed robbery as a juvenile and was later sentenced "
            "to life in prison without the possibility of parole for a probation violation, "
            "with no chance of release except executive clemency. The Supreme Court "
            "reversed the sentence, holding that the Eighth Amendment's prohibition on "
            "cruel and unusual punishment forbids sentencing a juvenile offender to life "
            "without parole for a non-homicide offense, and that the state must give "
            "juvenile non-homicide offenders a meaningful opportunity to obtain release "
            "based on demonstrated maturity and rehabilitation as part of parole "
            "eligibility. Graham is frequently cited in appeals and parole eligibility "
            "petitions brought by individuals who were sentenced as juveniles."
        ),
    },
]


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    role: str,
) -> User:
    """Create a user and return it."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
    )
    session.add(user)
    await session.flush()
    return user


async def seed() -> None:
    """Run seed: create 1 attorney, 1 paralegal, 1 inmate, 1 admin, 1 demo case shared to all but admin.

    Run after: alembic upgrade head
    """
    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # Create users
        attorney = await create_user(
            session,
            email="attorney@demo.local",
            password="demo123",
            full_name="Demo Attorney",
            role="attorney",
        )
        paralegal = await create_user(
            session,
            email="paralegal@demo.local",
            password="demo123",
            full_name="Demo Paralegal",
            role="paralegal",
        )
        inmate = await create_user(
            session,
            email="inmate@demo.local",
            password="demo123",
            full_name="Demo Inmate",
            role="inmate",
        )
        await create_user(
            session,
            email="admin@demo.local",
            password="demo123",
            full_name="Demo Admin",
            role="admin",
        )
        await session.flush()

        # Create demo case
        demo_case = Case(
            id=uuid.uuid4(),
            title="Demo Case",
            description="A sample case for demonstration purposes.",
            status="open",
            created_by_id=attorney.id,
        )
        session.add(demo_case)
        await session.flush()

        # Share case to all three users
        for user in (attorney, paralegal, inmate):
            share = Share(
                id=uuid.uuid4(),
                case_id=demo_case.id,
                user_id=user.id,
                role="viewer" if user.role == "inmate" else "editor",
            )
            session.add(share)

        # Seed a small verified-precedent starter set for /similar full-text search
        # (global entries, case_id=None — see PRECEDENT_OPINIONS docstring above).
        for entry in PRECEDENT_OPINIONS:
            session.add(Opinion(id=uuid.uuid4(), case_id=None, **entry))

        await session.commit()
        print("Seed complete: 1 attorney, 1 paralegal, 1 inmate, 1 admin, 1 demo case shared to attorney/paralegal/inmate.")
        print(f"  {len(PRECEDENT_OPINIONS)} precedent opinions seeded for /similar search")
        print("  attorney@demo.local / demo123")
        print("  paralegal@demo.local / demo123")
        print("  inmate@demo.local / demo123")
        print("  admin@demo.local / demo123")


if __name__ == "__main__":
    asyncio.run(seed())
