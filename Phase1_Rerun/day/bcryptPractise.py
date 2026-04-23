import bcrypt

password = 'SecurePass123'

#Hash it
encoded_pass = password.encode("utf-8")
hashed = bcrypt.hashpw(encoded_pass, bcrypt.gensalt(rounds=12))
print(hashed)
print(type(hashed))
stored_pwd = (hashed.decode("utf-8"))

print(stored_pwd)
print(type(stored_pwd))
#Verify correct password
print(bcrypt.checkpw(password.encode("utf-8"), hashed))

print(bcrypt.checkpw("Securepass123".encode('utf-8'), hashed))

hash1 = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
hash2 = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))

print(hash1 == hash2)