from passlib.hash import sha256_crypt

password = "password"

hashed = sha256_crypt.using(rounds=5000).hash(password)

print("Hashed password: ", hashed)
