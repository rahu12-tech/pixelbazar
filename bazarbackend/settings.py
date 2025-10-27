from pathlib import Path
import os
import environ
from datetime import timedelta

# ----------------------------------------
# 1️⃣ Base Directory
# ----------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------
# 2️⃣ Environment Setup (.env file ke liye)
# ----------------------------------------
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ----------------------------------------
# 3️⃣ Secret Key, Debug, Allowed Hosts
# ----------------------------------------
SECRET_KEY = env('SECRET_KEY', default='change-me-in-production')
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "").split(",") if host.strip()]
print("ALLOWED_HOSTS =>", ALLOWED_HOSTS)


# ----------------------------------------
# 4️⃣ Installed Apps
# ----------------------------------------
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',

    # Custom app
    'pixelbazar',
]

# ----------------------------------------
# 5️⃣ Middleware
# ----------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 👈 Static files ke liye
    'corsheaders.middleware.CorsMiddleware',  # 👈 sabse upar hona chahiye
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ----------------------------------------
# 6️⃣ CORS Setup (Frontend connection ke liye)
# ----------------------------------------
CORS_ALLOW_ALL_ORIGINS = True  # Local testing ke liye ✅

# 👇 Optional: sirf frontend port allow karna ho
CORS_ALLOWED_ORIGINS = [
    "https://pixelbazarfrontend.onrender.com",
    "http://localhost:5173",  # 👈 Vite frontend port
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ['*']
CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']

# ----------------------------------------
# 7️⃣ URL and WSGI
# ----------------------------------------
ROOT_URLCONF = 'bazarbackend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # frontend ke html ke liye
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bazarbackend.wsgi.application'

# ----------------------------------------
# 8️⃣ Database Setup
# ----------------------------------------
DATABASES = {
    'default': env.db(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# ----------------------------------------
# 9️⃣ Password Validators
# ----------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----------------------------------------
# 🔟 Django REST Framework + JWT Settings
# ----------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',  # 👈 Public endpoints by default
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),  # 7 days
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # 30 days
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,  # Allow refresh without blacklisting
    'AUTH_HEADER_TYPES': ('Bearer',),
    'UPDATE_LAST_LOGIN': True,
}

# ----------------------------------------
# 1️⃣1️⃣ Internationalization
# ----------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

AUTH_USER_MODEL = 'pixelbazar.User'



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = int(env('EMAIL_PORT', default=587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')       # .env me rakho
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')   # Gmail app password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or 'noreply@example.com'
GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID')

# ----------------------------------------
# Razorpay Configuration
# ----------------------------------------
RAZORPAY_KEY_ID = 'rzp_test_U3GGpYpzeFoRc5'
RAZORPAY_KEY_SECRET = 'xWsf3X2gpLNpbmSBnjZljOle'











# ----------------------------------------
# 1️⃣2️⃣ Static & Media Files
# ----------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise configuration for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Create static directory if it doesn't exist
STATIC_DIR = os.path.join(BASE_DIR, 'static')
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ----------------------------------------
# 1️⃣3️⃣ Default Auto Field
# ----------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
