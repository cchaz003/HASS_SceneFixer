import shutil
import time
import yaml
import paho.mqtt.client as mqtt
import os



MQTT_HOST = "YOUR.MQTT.HOST.IP"
MQTT_USER = 'YOUR MQTT USERNAME' #optional
MQTT_PASS = 'YOUR MQTT PASSWORD' #optional
MQTT_PORT = 1883
MQTT_TOPIC = "homeassistant/scenesUpdate"



#NOTE TO DOCKER FOLKS: Dont change this path as it's a local docker path.
#If you are using Docker, set your docker config folder in the docker-compose file
#
#Point this file to your scenes.yaml file
file = "/HASS/scenes.yaml"
bakFile = f'{file}.watcherBak'



class Handler():
    def __init__(self, filename, bakFilename):
        self.filename = filename
        self.bakFilename = bakFilename
        
        #create initial backup file
        shutil.copy(filename, bakFilename)

        self._cached_stamp = os.stat(self.filename).st_mtime
        self.ticker = 0         #keeps track of how long since pausing
        self.paused = False     #flag for tracking whether to process file modifications


    def loop(self):

        #check the mod time and update the ticker
        stamp = os.stat(self.filename).st_mtime
        self.ticker += 1

        #if file has been modified, run the handler
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            self.on_modified()

        #if the ticker has passed 5 ticks (5 seconds based on main's loop) and we are currently paused, then un-pause
        if(self.ticker >= 5 and self.paused):
            print("File monitoring un-paused.")
            self.paused = False
    




    def on_modified(self):


        if(not self.paused):
            #reset ticker and set paused flag
            self.ticker = 0
            self.paused = True

            print(f"Watchdog received modified event - {self.filename}.")
            print("File monitoring paused.")

            time.sleep(0.5)

            #run the fixer function and push MQTT msg if the file was fixed
            if(fixMissingEntities(self.filename, self.bakFilename)):
                notifyMQTT()
                print()
            
            #create a new backup file after any modification even if we didnt touch it
            #because we want to save good files too
            shutil.copy(self.filename, self.bakFilename)

            
            # Event is modified, you can process it now
            
  
'''
find and return a specific scene based 
on the scene's id in a list of scenes
'''
def findScene(scenesList, sceneID):
    for scene in scenesList:
        if(scene["id"] == sceneID):
            return scene
    return None

def fixMissingEntities(modifiedFile, backupFile):

    #open the modified file and backup and convert to lists of scenes (dicts)
    modYaml = []
    bakYaml = []
    with open(modifiedFile, 'r') as modFile:
        modYaml = yaml.safe_load(modFile)
    with open(backupFile, 'r') as bakFile:
        bakYaml = yaml.safe_load(bakFile)
    
    dataChanged = False

    #look through all scenes in the modified file
    for scene in modYaml:
        sceneName = scene["name"]
        sceneID = scene["id"]

        #look through all entities in the scene and find any that were saved as "unavailable"
        if('entities' in scene):
            for entityName in scene['entities'].keys():

                entity = scene['entities'][entityName]

                #if the entity was saved as unavailable, attempt to find the original state in the backup file and replace with that
                if('state' in entity and entity['state'] == 'unavailable'):
                    print(f"{entityName} in {sceneName} was marked as not available.")

                    origScene = findScene(bakYaml, sceneID)
                    
                    #check that we found the scene
                    if(origScene != None):
                        #check that we found the correct entity and update the scene as needed
                        if('entities' in origScene and entityName in origScene['entities']):
                            print("\tReplaced with data from backup file")
                            backupEntityData = origScene['entities'][entityName]
                            scene['entities'][entityName] = backupEntityData

                            #mark that we changed the modified file so that we can save a new version
                            dataChanged = True

                        else:
                            print("\tCould not locate entity in backup file scene.")

                    else:
                        print("\tCould not locate scene in backup file.")
    
    #save out the fixed file if needed
    if(dataChanged):
        saveYaml(modifiedFile, modYaml)
    
    return dataChanged


def saveYaml(filename, yamlList):
    print("Saving updated scene file.")
    with open(filename, 'w') as file:
        yaml.dump(yamlList, file)  



def notifyMQTT():
    print("Pinging MQTT")
    mqttClient = mqtt.Client()
    mqttClient.username_pw_set(MQTT_USER, MQTT_PASS)
    mqttClient.connect(MQTT_HOST, MQTT_PORT, 60)
    mqttClient.publish(MQTT_TOPIC, '1')



def main():
    print("\n\n\nStarting scenes fixer monitoring service.\n")
    watcher = Handler(file, bakFile)
    try:
        while True:
            time.sleep(1)
            watcher.loop()
    except KeyboardInterrupt:
        watcher.stop()



  
if __name__ == "__main__":
    main()