"""refactor categories to many-to-many

Revision ID: e2153238aa62
Revises: 210e21e25f57
Create Date: 2025-07-29 06:14:30.481586

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e2153238aa62'
down_revision = '210e21e25f57'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Таблица связки
    op.create_table(
        'user_categories',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'category_id')
    )

    # 2. Удаляем лишние колонки/индексы
    op.drop_index(op.f('ix_categories_user_id'), table_name='categories')
    op.drop_constraint(op.f('categories_user_id_fkey'),
                       'categories', type_='foreignkey')
    op.drop_column('categories', 'user_id')
    op.drop_column('categories', 'color')

    # 3. ЧИСТИМ ТАБЛИЦУ categories
    op.execute("TRUNCATE TABLE categories RESTART IDENTITY CASCADE")

    # 4. Делаем name уникальным
    op.create_unique_constraint('uq_categories_name',
                                'categories', ['name'])

    # 5. Загружаем полный список базовых категорий
    op.execute("""
        INSERT INTO categories (name, icon, is_income,
                                is_default, is_active, created_at)
        VALUES
            ('Еда',              '🍕', FALSE, TRUE, TRUE, now()),
            ('Транспорт',        '🚗', FALSE, TRUE, TRUE, now()),
            ('Жилье',            '🏠', FALSE, TRUE, TRUE, now()),
            ('Одежда',           '👕', FALSE, TRUE, TRUE, now()),
            ('Развлечения',      '🎬', FALSE, TRUE, TRUE, now()),
            ('Здоровье',         '💊', FALSE, TRUE, TRUE, now()),
            ('Образование',      '📚', FALSE, TRUE, TRUE, now()),
            ('Подарки',          '🎁', FALSE, TRUE, TRUE, now()),
            ('Связь',            '📱', FALSE, TRUE, TRUE, now()),
            ('Покупки',          '🛒', FALSE, TRUE, TRUE, now()),
            ('Зарплата',         '💼', TRUE,  TRUE, TRUE, now()),
            ('Подработка',       '💰', TRUE,  TRUE, TRUE, now()),
            ('Подарок',          '🎁', TRUE,  TRUE, TRUE, now()),
            ('Инвестиции',       '📈', TRUE,  TRUE, TRUE, now()),
            ('Возврат',          '💳', TRUE,  TRUE, TRUE, now()),
            ('Дети',             '🧒', FALSE, TRUE, TRUE, now()),
            ('Красота',          '💅', FALSE, TRUE, TRUE, now()),
            ('Кредит',           '💳', FALSE, TRUE, TRUE, now()),
            ('Кафе и Рестораны', '☕️', FALSE, TRUE, TRUE, now()),
            ('Подписки',         '🔔', FALSE, TRUE, TRUE, now()),
            ('Продукты',         '🛒', FALSE, TRUE, TRUE, now()),
            ('Путешествия',      '✈️', FALSE, TRUE, TRUE, now());
    """)

    # 6. Привязываем базовые категории всем пользователям
    op.execute("""
        INSERT INTO user_categories (user_id, category_id, created_at)
        SELECT u.id, c.id, now()
        FROM users u
        CROSS JOIN categories c
        WHERE c.is_default = TRUE;
    """)

def downgrade() -> None:
    # 1. Восстановить колонки user_id и color в categories
    op.add_column('categories', sa.Column('user_id', sa.INTEGER(), nullable=False))
    op.add_column('categories', sa.Column('color', sa.VARCHAR(length=7), nullable=True))

    # 2. Восстановить внешний ключ и индекс
    op.create_foreign_key(
        op.f('categories_user_id_fkey'),
        'categories', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index(op.f('ix_categories_user_id'), 'categories', ['user_id'], unique=False)

    # 3. Удалить уникальное ограничение на name
    op.drop_constraint('uq_categories_name', 'categories', type_='unique')

    # 4. Дропнуть таблицу user_categories
    op.drop_table('user_categories')