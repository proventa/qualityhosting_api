# Qualityhosting API
An API for Qualityhosting

# Example
```
#!/usr/bin/python
import QualityHosting

qh = QualityHosting.QualityHosting()

qh.login('12345\user','Password')
qh.createExchangeUser('testuser@example.com','Test','User','TempPasswd123')
user_id = qh.getExchangeUserId('testuser@example.com')
print qh.deleteExchangeUser(user_id)
```
