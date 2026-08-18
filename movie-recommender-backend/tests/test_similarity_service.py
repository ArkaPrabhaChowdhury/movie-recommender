import unittest

from services.similarity_service import rank_similar_content, similarity_score, story_similarity


class SimilarityServiceTests(unittest.TestCase):
    source = {
        "id": 1,
        "content_type": "movie",
        "genres": [{"id": 28}, {"id": 53}],
        "original_language": "en",
        "overview": "A family trapped inside their home must survive a mysterious threat and dwindling resources.",
    }

    def test_story_and_genre_match_beats_popularity(self):
        strong = {
            "id": 2, "content_type": "movie", "poster": "strong.jpg",
            "genre_ids": [28, 53], "overview": "A family trapped inside a house must survive a mysterious threat and dwindling resources.",
            "streaming": {"platform_found": True},
        }
        weak = {
            "id": 3, "content_type": "movie", "poster": "weak.jpg",
            "genre_ids": [28, 53], "overview": "A time traveller returns to the future and changes history.",
            "is_trending": True, "streaming": {"platform_found": True},
        }
        self.assertGreater(story_similarity(self.source | {"overview": strong["overview"]}, strong), 0)
        self.assertGreater(similarity_score(self.source, strong), similarity_score(self.source, weak))
        self.assertEqual([item["id"] for item in rank_similar_content(self.source, [weak, strong])], [2])

    def test_filters_source_duplicates_missing_posters_and_unavailable_titles(self):
        candidates = [
            {"id": 1, "content_type": "movie", "poster": "source.jpg"},
            {"id": 2, "content_type": "movie", "poster": None},
            {"id": 3, "content_type": "movie", "poster": "unavailable.jpg", "streaming": {"platform_found": False}},
            {"id": 4, "content_type": "movie", "poster": "good.jpg", "genre_ids": [28], "overview": "A family trapped inside a home must survive a mysterious threat.", "streaming": {"platform_found": True}},
            {"id": 4, "content_type": "movie", "poster": "duplicate.jpg", "genre_ids": [28], "overview": "A family trapped inside a home must survive a mysterious threat.", "streaming": {"platform_found": True}},
        ]
        result = rank_similar_content(self.source, candidates)
        self.assertEqual([item["id"] for item in result], [4])


if __name__ == "__main__":
    unittest.main()
