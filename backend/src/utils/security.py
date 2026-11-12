import hashlib,hmac,secrets
import jwt
from datetime import datetime,timedelta,timezone
from src.config.settings import JWT_SECRET
def hash_password(password):
    salt=secrets.token_hex(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),120000).hex()
    return salt+':'+digest
def check_password(password,stored):
    salt,digest=stored.split(':')
    return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),120000).hex(),digest)
def token_for(user):
    return jwt.encode({'sub':str(user.id),'exp':datetime.now(timezone.utc)+timedelta(hours=8)},JWT_SECRET,algorithm='HS256')
