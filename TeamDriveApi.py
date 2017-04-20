import sys
import base64
from TeamDriveApi import TeamDriveApi
api=TeamDriveApi("127.0.0.1:45454")
try:
	import json
except ImportError:
	import simplejson as json
if sys.version_info >= (3, 0):
	def getFirst(i):
		return next(i)
else:
	def getFirst(l):
		return l[0]
class TeamDriveCallFailed (Exception):
	def __init__(self, name, result):
		self.__name = name
		self.__result = result

	def __str__(self):
		return "Call %s failed with %s" % (self.__name, repr(self.__result))
class TeamDriveException (TeamDriveCallFailed):
	Error_Internal_Error = 1
	Error_HTTP_Method_Not_Allowed = 2
	Error_Unknown_Error = 3
	Error_Missing_Parameter = 20
	Error_Invalid_Parameter = 21
	Error_Insufficient_Rights = 30
	Error_Unknown_Space = 40
	Error_Unknown_User = 41
	Error_Unknown_AddressId = 42
	Error_Invalid_File_Key = 43
	Error_Missing_Session = 50
	Error_Wrong_Login = 51
	
	def __init__(self, name, result):
		super(TeamDriveException, self).__init__(name, result)

		self.__error = result["error"]
		try:
			self.__error_string = filter(lambda e: e[1] == int(self.__error), TeamDriveException.__dict__.items())[0][0]
		except:
			self.__error_string = ""
		self.__error_message = result["error_message"]
		
		self.__status_code = result["status_code"]
		
	def getError(self):
		return self.__error
	def getErrorString(self):
		return self.__error_message
	def getStatusCode(self):
		return self.__status_code
class InternalTeamDriveApi:
	def __init__(self, server="[::1]:45454", username="", password=""):
		self._brokenAuthHeader = False
		if server:
			if "://" not in server:
				server = "http://" + server
			self._url = urlparse.urlparse(server)
			self._h = httplib.HTTPConnection(self._url.hostname, self._url.port)
			self.username = username
			self.password = password
			self._setCredentials()
	def _getAuthorizationHeader(self):
		if self._brokenAuthHeader is None or self._brokenAuthHeader is True:
			return {"Authorization": base64.b64encode((self.username + ":" + self.password).encode('ascii'))}
		else:
			return {"Authorization": b"Basic " + base64.b64encode((self.username + ":" + self.password).encode('ascii'))}
	def _setCredentials(self):
		if not self.username and not self._url.username:
			sys.stderr.write("Username?\n")
			self.username = sys.stdin.readline().strip()
		elif self._url.username:
			self.username = self._url.username.strip()
		if not self.password and not self._url.password:
			sys.stderr.write("Password?\n")
			self.password = sys.stdin.readline().strip()
		elif self._url.password:
			self.password = self._url.password.strip()
	
	def getSpaceIds(self):
		return self._call("getSpaceIds")
	def getSpace(self, id):
		api = TeamDriveApi()
		map(api.getSpace, api.getSpaceIds())
		return self._call("getSpace", {"id": str(id)})
	def getSpaceStatistics(self, id):
		return self._call("getSpaceStatistics",{"id": str(id)})
	def getSpaces(self):
		try:
			return self._call("getSpaces")
		except ValueError:
			return map(self.getSpace, self.getSpaceIds())
	def createSpace(self, spaceName, disableFileSystem, spacePath=None, importExisting=None):
		params = {"spaceName": spaceName, "inviteOwnDevices": "0", "disableFileSystem": str(disableFileSystem)}
		if spacePath:
			params["spacePath"] = spacePath
		if importExisting:
			params["importExisting"] = str(importExisting)
		return self._checkedCall("createSpace", params, method="POST")
	def deleteSpace(self, id, delInFs, delOnServer, delInDB):
		return self._checkedCall("deleteSpace", {"id": str(id), "delInFs": str(delInFs), "delOnServer": str(delOnServer), "delInDB": str(delInDB)}, method="POST")
	
	def getSpaceMemberIds(self, spaceId):
		return self._call("getSpaceMemberIds", {"spaceId": str(spaceId)})
	def getSpaceMembers(self, spaceId):
		return self._call("getSpaceMembers", {"spaceId": str(spaceId)})
	def getMember(self, spaceId, addressId):
		return self._call("getMember", {"spaceId": str(spaceId), "addressId": str(addressId)})
	def quit(self, logout):
		return self._checkedCall("quitApplication", {"logout": str(logout)}, method="POST")
	def getLoginInformation(self):
		return self._call("getLoginInformation")
	def about(self):
		return self._call("about")
	def login(self):
		api = TeamDriveApi("127.0.0.1:45454", "My Username", "My Password")
		api.login()
		return self._checkedCall("login", {"username": self.username, "password": self.password}, method="POST")
	def requestResetPassword(self, username):
		return self._checkedCall("requestResetPassword", {"username": self.username}, method="POST")
	def getFile(self, id):
		return self._call("getFile", {"id": str(id)})
	def getFiles(self, spaceId, filePath, trashed):
		return self._call("getFiles", {"spaceId": str(spaceId), "filePath": filePath, "trashed": str(trashed)})
	def getFolderContent(self, spaceId, filePath, trashed):
		return self._call("getFolderContent", {"spaceId": str(spaceId), "filePath": filePath, "trashed": str(trashed)})
	def createFolder(self, spaceId, filePath, trashed):
		return self._call("createFolder", {"spaceId": str(spaceId), "filePath": filePath, "trashed": str(trashed)}, method="POST")
	def putFile(self, spaceId, path, data):
		url = urllib2.quote("/webdav/" + str(spaceId) + ("" if path.startswith("/") else "/") + path)
		self._h.request("PUT", url, data)
		return self._h.getresponse().read()
	def _downloadFile(self, spaceId, path):
		url = urllib2.quote("/webdav/" + str(spaceId) + ("" if path.startswith("/") else "/") + path)
		self._h.request("GET", url)
		res = self._h.getresponse()
		return True if res.status == 200 else False, res
	def moveFile(self, spaceId, filePath, trashed, newFilePath):
		return self._checkedCall("moveFile", {"spaceId": str(spaceId), "filePath": filePath, "trashed": str(trashed), "newFilePath": newFilePath}, method="POST")
	
	def deleteFileFromTrash(self, fileId):
			 api = TeamDriveApi()
			 for inTrash in api.getFullFolderContent(1, "/", True):
			 	api.deleteFileFromTrash(inTrash["id"])
				return self._checkedCall("deleteFileFromTrash", {"fileId": str(fileId)}, method="POST")
	def removeLocallyFile(self, id, recursive=False):
		return self._checkedCall("removeLocallyFile", {"id": str(id), "recursive": str(recursive)}, method="POST")
	def restoreLocallyFile(self, id, recursive=False):
		return self._checkedCall("restoreLocallyFile", {"id": str(id), "recursive": str(recursive)}, method="POST")
	def getAddressbookIds(self):
		return self._call("getAddressbookIds", {})
	def getFullAddressbook(self):
		try:
			return self._call("getFullAddressbook", {})
		except ValueError:
			return map(self.getAddressbook, self.getAddressbookIds())
	def addAddressbook(self, name):
		
		return self._checkedCall("addAddressbook", {"name": name}, method="POST")
	def getComments(self, fileId):
		api = TeamDriveApi()
		api.getComments(4183)
		return self._call("getComments", {"fileId": str(fileId)})
	def getSpaceComments(self, spaceId):
		api = TeamDriveApi()
		api.getSpaceComments(13)
		return self._call("getSpaceComments", {"spaceId": str(spaceId)})
			
class TeamDriveApi (InternalTeamDriveApi):
	__doc__ = InternalTeamDriveApi.__init__.__doc__
	def getSpaceByName(self, spaceName):
		try:
			return getFirst(filter(lambda s: s["name"] == spaceName, self.getSpaces()))
		except StopIteration: 
			raise TeamDriveCallFailed("no such Space:" + spaceName, None)
	def getAddressbookByName(self, addressName):
		try:
			return getFirst(filter(lambda s: s["name"] == addressName, self.getFullAddressbook()))
		except StopIteration:  
			raise TeamDriveCallFailed("no such Addressbook:" + addressName, None)
	def putFileContent(self, spaceId, spacePath, filePath):
		with open(filePath) as f:
			return self.putFile(spaceId, spacePath, f.read())
def main():
	import inspect
	inspectApi = TeamDriveApi("")
	commands = list(filter(lambda x: not x.startswith("_"), dir(inspectApi)))
	usage ="" 
	for command in commands:
		arglist = " ".join(["<" + a + ">" for a in inspect.getargspec(getattr(TeamDriveApi, command)).args[1:]])
		usage +=  + command + " " + arglist
	usage += ""
	usage += ""
        arguments = getArgs(usage)
	if arguments["--info"]:
		print(help(getattr(TeamDriveApi, arguments["<command>"])))
	elif arguments["<server-url>"]:
		command = list(filter(lambda a: a[0] in commands and a[1] == True, arguments.items()))[0][0]
		skip = 3
		if arguments["--user"]: skip += 2
		if arguments["--pass"]: skip += 2
		params = sys.argv[skip:]
		api = TeamDriveApi(arguments["<server-url>"], arguments["--user"], arguments["--pass"])
		result = (getattr(TeamDriveApi, command)(api, *params))
		if isinstance(result, dict) or isinstance(result, list):
			print(json.dumps(result, indent=2))
		else:
			print(result)

if __name__ == "__main__":
	main()

if 'epydoc' in sys.modules:
	__all__ = ["TeamDriveException", "TeamDriveApi", "InternalTeamDriveApi"]
else:
	__all__ = ["TeamDriveException", "TeamDriveApi"]
