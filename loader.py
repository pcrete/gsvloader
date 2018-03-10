from PIL import Image
from urllib.request import urlopen, HTTPError
from io import BytesIO
from tqdm import tqdm
import json
import os

key_index = 0

DEGREES = None

def run(entry, points):
    if not os.path.exists(entry['OUTPUT_IMAGE_PATH']): 
        os.makedirs(entry['OUTPUT_IMAGE_PATH'])

    for lat, lng in tqdm(points, 'loading GSV'):
        loading(lat, 
                lng, 
                entry['OUTPUT_IMAGE_PATH'], 
                entry['keys'], 
                entry['degrees'], 
                str(entry['fov']), 
                str(entry['pitch']),
                str(entry['width']),
                str(entry['height'])
                )    
                
    # print('GSV loaded')

def loading(lat, lng, path, keys, heads, fov, pitch, width, height): 
    global key_index 

    j = 0 
    check = False
    while not check: 
        location = str(lat)+','+str(lng) 
        try: 
            key = keys[key_index] 
            baseMetaUrl = "https://maps.googleapis.com/maps/api/streetview/metadata" 
            metaUrl = baseMetaUrl+"?location="+location+"&fov="+fov+"&pitch="+pitch+"&key="+key 
            requestMeta = urlopen(metaUrl)    
            metaJson = json.loads(requestMeta.read().decode('utf8'))

            if metaJson["status"] == 'OK': 
                for heading in heads:
                    heading = str(heading)
                    lat, lng = str(metaJson["location"]["lat"]), str(metaJson["location"]["lng"]) 
                    coordinate = lat+','+lng
                    baseImgUrl = "https://maps.googleapis.com/maps/api/streetview?size="+width+"x"+height 
                    imgUrl = baseImgUrl+"&location="+coordinate+"&fov="+fov+"&heading="+heading+"&pitch="+pitch+"&key="+key 
                    requestImg = urlopen(imgUrl) 
                    image = Image.open(BytesIO(requestImg.read())) 
                    
                    image.save(path +'/'+str(round(float(lat),8))+'_'+str(round(float(lng),8))+'_'+heading+'_'+metaJson["date"]+'.jpg') 
            
            check = True 
        except HTTPError as e: 
            key_index += 1 
            print('Change Key Index to '+str(key_index)) 
            if key_index>len(keys)-1:  
                print(lat,lng,path) 
                break 
            print('Forbidden', str(e.getcode()), ':', imgUrl) 
            continue