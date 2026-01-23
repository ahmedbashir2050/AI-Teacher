from services.scoring_service import scoring_service

def test_scoring_logic():
    exam_content = {
        "sections": [
            {
                "section_id": "matching_1",
                "type": "matching",
                "questions": [
                    {"pair_id": 1, "item_a": "A1", "item_b": "B1"},
                    {"pair_id": 2, "item_a": "A2", "item_b": "B2"},
                    {"pair_id": 3, "item_a": "A3", "item_b": "B3"},
                    {"pair_id": 4, "item_a": "A4", "item_b": "B4"},
                    {"pair_id": 5, "item_a": "A5", "item_b": "B5"},
                ]
            },
            {
                "section_id": "tf",
                "type": "tf",
                "questions": [
                    {"id": 1, "correct_answer": True},
                    {"id": 2, "correct_answer": False},
                ]
            },
            {
                "section_id": "mcq",
                "type": "mcq",
                "questions": [
                    {"id": 1, "correct_answer": "Option1"},
                ]
            }
        ]
    }

    student_answers = {
        "matching_1": [
            {"pair_id": 1, "item_b_answer": "B1"}, # correct +4
            {"pair_id": 2, "item_b_answer": "Wrong"}, # incorrect
        ],
        "tf": [
            {"id": 1, "answer": True}, # correct +2
            {"id": 2, "answer": True}, # incorrect
        ],
        "mcq": [
            {"id": 1, "answer": "Option1"}, # correct +4
        ]
    }

    total_score, section_scores = scoring_service.calculate_score(exam_content, student_answers)

    assert section_scores["matching_1"] == 4
    assert section_scores["tf"] == 2
    assert section_scores["mcq"] == 4
    assert total_score == 10

def test_full_correct_score():
    exam_content = {
        "sections": [
            {
                "section_id": "matching_1",
                "type": "matching",
                "questions": [{"pair_id": i, "item_b": f"B{i}"} for i in range(1, 6)]
            },
            {
                "section_id": "matching_2",
                "type": "matching",
                "questions": [{"pair_id": i, "item_b": f"B{i}"} for i in range(1, 6)]
            },
            {
                "section_id": "tf",
                "type": "tf",
                "questions": [{"id": i, "correct_answer": True} for i in range(1, 11)]
            },
            {
                "section_id": "mcq",
                "type": "mcq",
                "questions": [{"id": i, "correct_answer": "A"} for i in range(1, 11)]
            }
        ]
    }

    student_answers = {
        "matching_1": [{"pair_id": i, "item_b_answer": f"B{i}"} for i in range(1, 6)],
        "matching_2": [{"pair_id": i, "item_b_answer": f"B{i}"} for i in range(1, 6)],
        "tf": [{"id": i, "answer": True} for i in range(1, 11)],
        "mcq": [{"id": i, "answer": "A"} for i in range(1, 11)]
    }

    total_score, section_scores = scoring_service.calculate_score(exam_content, student_answers)

    assert section_scores["matching_1"] == 20
    assert section_scores["matching_2"] == 20
    assert section_scores["tf"] == 20
    assert section_scores["mcq"] == 40
    assert total_score == 100
