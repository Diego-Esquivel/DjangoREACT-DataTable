import uuid
from django.db import models

# Create your models here.

class TimeSeriesListPendingData_0_0_1(models.Model):
        time_polled = models.DateTimeField(db_column="Time_of_Record",editable=False,db_index=False)
        queue_size = models.PositiveBigIntegerField()

        def __str__(self):
                return "At time: " + str(self.time_polled) + "\tWe had: " +  str(self.queue_size) + " items in queue"

# Platforms_0_0_1: A model to manage the table for farm board & test platforms.
#       name - The name for the platform
class Platforms_0_0_1(models.Model):
        name = models.TextField(db_column="Platform_Name",db_index=True,unique=True,editable=False,primary_key=True)

        class Meta:
                ordering = ['name']
        def __str__(self):
                return self.name

# Capabilities_0_0_1: A model to manage the table for farm board & test capabilities.
#       name - The name for the capability
class Capabilities_0_0_1(models.Model):
        name = models.TextField(db_column="Capability_Name",db_index=True,unique=True,editable=False,primary_key=True)

        class Meta:
                ordering = ['name']
        def __str__(self):
                return self.name

class PollTimestamp_0_0_1(models.Model):
       pollTime = models.TextField(db_column="Time_Polled",editable=False,db_index=True,primary_key=True)
       def __str__(self):
              return self.pollTime

# Listpending_0_0_1: A model to manage the table for farm tests in the Listpending STAF response.
#       handle - The handle requested by a test.
#       platform - The platform requested by a test.
#       pollTimestamp - The time the STAF service was polled for data.
#       capabilities - The capabilities requested by a test.
#       id - A UUID for the test instance. This is the primary key.
class Listpending_0_1_0(models.Model):
        handle = models.TextField(db_column="Test_Handle",editable=False)
        platform = models.ManyToManyField(Platforms_0_0_1)
        pollTimestamp = models.ForeignKey(PollTimestamp_0_0_1,on_delete=models.CASCADE)
        capabilities = models.ManyToManyField(Capabilities_0_0_1)
        id = models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True)

        class Meta:
                ordering = ["pollTimestamp"]
        def __str__(self):
                capabilities_set = self.capabilities.all()
                capabilities_str = ""
                for i in capabilities_set:
                        capabilities_str += str(i) + '_'
                return "Handle " + self.handle + " has capabilities: " + (capabilities_str)
        def __iter__(self):
                platforms_str = []
                capabilities_str = []
                platforms_set = self.platform.all()
                capabilities_set = self.capabilities.all()
                for i in capabilities_set:
                    capabilities_str.append(str(i))
                capabilities_str = ", ".join(capabilities_str)
                for i in platforms_set:
                    platforms_str.append(str(i))
                platforms_str = ", ".join(platforms_str)
                return {"handle":self.handle,"platform":platforms_str,"pollTimestamp":self.pollTimestamp.pollTime,"capabilities":capabilities_str}

# FarmBoards_0_0_1: A model to manage the table for farm boards in the List STAF response.
#       name_type - The board name. It is made by concatenating the name & type returned in the STAF response.
#       capabilities - The capabilities requested by a test.
#       platform - The platform on the board.
#       id - A UUID for the test instance. This is the primary key.
#       added_datetime - The time the board was noticed by this program.
#       modified_datetime - The time the board was no longer noticed by this program.
class FarmBoards_0_0_1(models.Model):
        name_type = models.TextField(db_column="Board_Name",editable=False)
        capabilities = models.ManyToManyField(Capabilities_0_0_1)
        platform = models.ManyToManyField(Platforms_0_0_1)
        id = models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True)
        added_datetime = models.DateTimeField(db_column="Added_Date",editable=False,db_index=False)
        modified_datetime = models.DateTimeField(blank=True,null=True,db_column="Removed_Or_Updated_Date",editable=False,db_index=False)
        
        class Meta:
                ordering = ["name_type","added_datetime"]
                
        def __str__(self):
                capabilities_set = self.capabilities.all()
                capabilities_str = ""
                for i in capabilities_set:
                        capabilities_str += str(i) + '_'
                return "Farm Board " + self.name_type + " has capabilities: " + capabilities_str
        def __iter__(self):
                platforms_str = []
                capabilities_str = []
                platforms_set = self.platform.all()
                capabilities_set = self.capabilities.all()
                for i in capabilities_set:
                    capabilities_str.append(str(i))
                capabilities_str = ', '.join(capabilities_str)
                for i in platforms_set:
                    platforms_str.append(str(i))
                platforms_str = ', '.join(platforms_str)
                return {"name_type":self.name_type,"platform":platforms_str,"active":("True" if self.modified_datetime == None else "False"),"capabilities":capabilities_str}
