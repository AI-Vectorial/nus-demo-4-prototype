"""The fixed evaluation set, from corpus/EVALUATION.md.

Question wording is taken from that file. Expected sections are matched on the
document id and the section number (e.g. "4.2"), so a heading renamed in
wording does not break the check, and a wrong section does.

Protected content: if a question fails, fix retrieval. Do not edit these to fit.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    # Each entry is (document_id, section number). A question passes when every
    # listed item appears in the top three results. Q8 accepts either section.
    expected: tuple[tuple[str, str], ...] = ()
    any_of: tuple[tuple[str, str], ...] = field(default=())
    answerable: bool = True


TRAVEL = "travel-expense-policy"
KYC = "client-onboarding-kyc"
RETENTION = "records-retention"
OUTSOURCING = "outsourcing-third-party"

QUESTIONS: tuple[Question, ...] = (
    Question("Q1", "What is the approval threshold for a travel expense claim?",
             expected=((TRAVEL, "4.2"),)),
    Question("Q2", "Does a claim of exactly £75 need approval?",
             expected=((TRAVEL, "4.2"),)),
    Question("Q3", "Can I fly business class on a six-hour flight?",
             expected=((TRAVEL, "5.2"),)),
    Question("Q4", "What is the accommodation cap for a night in Singapore?",
             expected=((TRAVEL, "6.2"),)),
    Question("Q5", "How often do we refresh KYC for a high-risk client?",
             expected=((KYC, "6.1"),)),
    Question("Q6", "What happens if a KYC refresh is more than 90 days overdue?",
             expected=((KYC, "6.4"),)),
    Question("Q7", "At what ownership percentage do we identify beneficial owners "
                   "under enhanced due diligence?",
             expected=((KYC, "4.2"),)),
    Question("Q8", "How long do we keep client correspondence?",
             any_of=((RETENTION, "4.1"), (RETENTION, "4.2"))),
    Question("Q9", "Who can approve a critical outsourcing arrangement?",
             expected=((OUTSOURCING, "4.1"),)),
    # Q10 is the conflict. Both sides must surface (D1 check, criterion 6).
    Question("Q10", "A provider holds our client correspondence. How long can they keep "
                    "it after we terminate?",
             expected=((OUTSOURCING, "6.4"), (RETENTION, "4.1"))),
    Question("Q11", "Can I expense my partner's flight if they travel with me?",
             answerable=False),
    Question("Q12", "What is our policy on cryptocurrency held by clients?",
             answerable=False),
    Question("Q13", "How many days of paid parental leave am I entitled to?",
             answerable=False),
)
