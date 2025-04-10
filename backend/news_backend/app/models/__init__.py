from app.models.user import User, UserRegistrationSchema, UserResponseSchema
from app.models.news_detection import NewsDetectionHistory, news_detection_schema, news_detections_schema
from app.models.news_generation import NewsGenerationHistory, news_generation_schema, news_generations_schema
from app.models.news_summary import NewsSummaryHistory, news_summary_schema, news_summaries_schema
from app.models.news_statistics import (
    NewsStatistics, news_stats_schema,
    NewsStatisticsByUser, news_stats_by_user_schema, news_stats_by_users_schema
) 