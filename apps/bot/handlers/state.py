"""Bot foydalanuvchilarining joriy holatlari va sessiyalari."""

# user_id -> "CITIZEN" | "ADMIN"
USER_ROLES: dict[int, str] = {}

# Tasdiqlangan admin user_id lar to'plami
ADMIN_SESSIONS: set[int] = set()

# user_id -> oxirgi yaratilgan incident_id (bekor qilish imkoniyati uchun)
LAST_USER_INCIDENTS: dict[int, int] = {}

# user_id -> tasdiqlangan telefon raqami
USER_PHONES: dict[int, str] = {}

