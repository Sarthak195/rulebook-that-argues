# Planted contradictions

Three contradictions were written into the corpus on purpose. This file is the answer key;
the system never reads it. Each one is a clean numeric disagreement about the same situation,
spread across different documents and formats, because that is how real rulebooks contradict
themselves: nobody reads the fee table and the scholarship PDF at the same time.

| # | Topic | Clause A | Clause B | Formats |
|---|---|---|---|---|
| C1 | Lowest attendance that can be condoned on medical grounds | **AR §4.3** (Academic Regulations): not less than **65 per cent**, "shall not be condoned under any circumstances" below that | **LM §2.2** (Leave and Medical Policy): not less than **55 per cent** | markdown vs markdown |
| C2 | Tuition refund on withdrawal before classes commence | **FS §4.1** (Fee Schedule, refund table): **100 per cent** refunded | **SF §6.2** (Scholarship policy, PDF): refunded after a **10 per cent processing charge**, i.e. 90 per cent | markdown table vs PDF |
| C3 | CGPA needed to keep the Merit Scholarship | **AR §11.2** (Academic Regulations): not less than **7.5** each semester | **SF §3.1** (Scholarship policy, PDF): not less than **8.0** each semester | markdown vs PDF |

## Deliberate non-contradictions (distractors)

These look like conflicts to a careless reader and the system must **not** flag them:

- **AR §14.1** lets the Academic Council relax any provision. A waiver power is not a contradiction.
- **AR §15.1** makes the Vice-Chancellor the final authority on inconsistencies. This is the clause the
  system surfaces as "who can resolve this" when it does detect a conflict.
- **AR §4.1** (75 per cent minimum attendance) and **AR §4.3 / LM §2.2** (condonation floors) address
  different questions: the base requirement versus how far a medical shortfall can be condoned.
  A question about the base requirement should be *answered*, not flagged.
- **AR §8.1** and **EE §7.1** both describe supplementary examinations and agree with each other.
- **AR §9.1** and the **FS §2.1** table both say re-evaluation applications are due within 10 working days.
