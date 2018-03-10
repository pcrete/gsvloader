from shapely.geometry import Polygon, Point, LineString
import numpy as np
import json
from tqdm import tqdm
import os
import time
import math
import overpass
from time import sleep

def run(entry, geojson_prop):
	polygon = get_polygon(entry, geojson_prop)
	if(polygon != 'error'):
		return extract_coordinates(polygon)
	return None

def get_polygon(entry, geojson_prop):
	with open(entry['GEOJSON_PATH'], encoding='utf8') as f:
		data = json.load(f)
	# print('Imported GeoJSON')

	for feature in data['features']:
		props = feature['properties']
		match = True
		for att in geojson_prop:
			if props[att] != geojson_prop[att]:
				match = False
		if(match):
			print([geojson_prop[att] for att in geojson_prop])
			coords = feature['geometry']['coordinates'][0]
			# print('Coordinates:', coords.shape)
			return Polygon(coords)
	    
	print('polygon not loaded')
	return 'error'

def extract_coordinates(polygon):
	data = generate_overpass_script(polygon)
	# print('retrieved linestrings (roads) from overpass api')
	multiline = []
	for feature in data['features']:
		if (feature['geometry']['type'] == 'LineString'):
			multiline.append(feature['geometry']['coordinates'])
	points = linestring_to_coords(multiline)
	# print('linestring: '+str(len(multiline))+' lines')
	# print('total points: '+str(len(points))+'points')
	return points

def generate_overpass_script(polygon):
	api = overpass.API(timeout=100)
	query = '(\nway[highway](poly:"'    
	# convert polygon to coordinates (longitude, latitude)
	coords = list(polygon.exterior.coords)
	for coord in coords:
		lng, lat =  coord
		query += str(lat)+' '+str(lng)+' '
	query = query[:-1] + '");\n);'
	return api.Get(query)

def linestring_to_coords(multiline):
	points = []
	for line in tqdm(multiline,'converting linestrings to coordinates'):
		for i in range(len(line)-1):
			x1,y1 = line[i]
			x2,y2 = line[i+1]
			x1 += 0.0000000001

			degree = math.degrees(math.atan(abs((y1-y2)/(x1-x2))))
            
			if(degree < 45): 
				if(x1 == min(x1,x2)): start_x,start_y, end_x,end_y = x1,y1, x2,y2 
				else: start_x,start_y, end_x,end_y = x2,y2, x1,y1
                    
				m = (start_y-end_y)/(start_x-end_x)
				FROM, TO = start_x, end_x                      
				cur_x, cur_y = start_x, start_y
				while(FROM < TO):
					new_x, new_y = linearEquation_x(start_x, start_y, m, FROM)
					dist = math.hypot(new_x-cur_x, new_y-cur_y)
					meters = 111111*dist
					if(meters > 50):
						cur_x, cur_y = new_x, new_y
						points.append([round(cur_y, 8), round(cur_x, 8)])  
					FROM += 0.000000123
			else:
				if(y1 == min(y1,y2)): start_x,start_y, end_x,end_y = x1,y1, x2,y2 
				else: start_x,start_y, end_x,end_y = x2,y2, x1,y1
	
				m = (start_y-end_y)/(start_x-end_x)
				FROM, TO = start_y, end_y                      
				cur_x, cur_y = start_x, start_y
				while(FROM < TO):
					new_x, new_y = linearEquation_y(start_x, start_y, m, FROM)
					dist = math.hypot(new_x-cur_x, new_y-cur_y)
					meters = 111111*dist
					if(meters > 50):
						cur_x, cur_y = new_x, new_y
						points.append([round(cur_y, 8), round(cur_x, 8)])  
					FROM += 0.000000123
	return points

def linearEquation_x(x1, y1, m, x):
	y = m*(x-x1)+y1
	return x,y

def linearEquation_y(x1, y1, m, y):
	x = (y - y1 + (m*x1)) / m
	return x,y