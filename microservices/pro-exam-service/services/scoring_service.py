class ScoringService:
    def calculate_score(self, exam_content: dict, student_answers: dict) -> tuple[int, dict]:
        """
        Calculates the score for a professional exam based on exactly 4 sections.
        - Matching (matching_1): 5 questions * 4 pts = 20 pts
        - Matching (matching_2): 5 questions * 4 pts = 20 pts
        - True/False (tf): 10 questions * 2 pts = 20 pts
        - MCQ (mcq): 10 questions * 4 pts = 40 pts
        Total: 100 points.
        """
        total_score = 0
        section_scores = {}

        for section in exam_content.get("sections", []):
            section_id = section["section_id"]
            section_type = section["type"]
            answers = student_answers.get(section_id, [])

            s_score = 0
            if section_type == "matching":
                # student answers for matching: list of { "pair_id": ..., "item_b_answer": ... }
                correct_pairs = {q["pair_id"]: q["item_b"] for q in section["questions"]}
                for ans in answers:
                    if correct_pairs.get(ans.get("pair_id")) == ans.get("item_b_answer"):
                        s_score += 4
            elif section_type == "tf":
                # student answers for tf: list of { "id": ..., "answer": bool }
                correct_tf = {q["id"]: q["correct_answer"] for q in section["questions"]}
                for ans in answers:
                    if correct_tf.get(ans.get("id")) == ans.get("answer"):
                        s_score += 2
            elif section_type == "mcq":
                # student answers for mcq: list of { "id": ..., "answer": ... }
                correct_mcq = {q["id"]: q["correct_answer"] for q in section["questions"]}
                for ans in answers:
                    if correct_mcq.get(ans.get("id")) == ans.get("answer"):
                        s_score += 4

            section_scores[section_id] = s_score
            total_score += s_score

        return total_score, section_scores

scoring_service = ScoringService()
