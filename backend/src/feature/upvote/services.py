# Python standard library
from sqlalchemy import delete, insert, select

# Local imports
from src.models import user_news_association_table

def get_article_upvote_details(article_id, user_id, database):
    upvote_count = (
        database.query(user_news_association_table)
        .filter_by(news_articles_id=article_id)
        .count()
    )
    is_upvoted = False
    if user_id:
        is_upvoted = (
                database.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=user_id)
                .first()
                is not None
        )
    return upvote_count, is_upvoted

def toggle_upvote(news_id, user_id, database):
    existing_upvote = database.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
    ).scalar()

    if existing_upvote:
        delete_stmt = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
        database.execute(delete_stmt)
        database.commit()
        return "Upvote removed"
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=news_id, user_id=user_id
        )
        database.execute(insert_stmt)
        database.commit()
        return "Article upvoted"
