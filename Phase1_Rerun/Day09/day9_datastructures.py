services = ["nginx", "mysql", "redis"]
services.append("unix")
services.remove("redis")
print(services[0:3])
server_info = ("10.0.0.5", 443)
(ip, port) = server_info
admins = {"jay", "mary", "paul"}
devs = {"mary", "paul", "alex"}
print(admins | devs)
print(admins & devs)
print(admins - devs)

