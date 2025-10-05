import uuid
from datetime import datetime, timedelta
from pyproj import Transformer

# ====== CONFIG ======
contact_callsign = "FOKZ-nav"
cot_point_type = "b-m-p"
# a-f-G-U-C	Default “unit” point, generic mobile object
# b-m-p	Position of a person
# b-f-G-U-C	Friendly unit
# b-a	Aircraft / air asset
# b-t	Track / sensor track
# b-m	Mounted vehicle
# b-n	Neutral unit
# b-h	Hostile unit
# p-p
origin_lat = 50.0678231   # your initial reference latitude
origin_lon = 19.9915486   # your initial reference longitude

# Setup transformer: local meters (East/North) -> lat/lon
transformer = Transformer.from_crs(
    f"+proj=aeqd +lat_0={origin_lat} +lon_0={origin_lon} +units=m +datum=WGS84",
    "EPSG:4326",
    always_xy=True
)

def create_cot_event(lat, lon, cot_type=cot_point_type):
    """
    Generate a CoT XML string for given lat/lon.
    """
    now = datetime.utcnow()
    stale = now + timedelta(minutes=5)
    uid = str(uuid.uuid4())

    cot_xml = f'''<event version="2.0" type="{cot_type}" uid="{uid}" 
       time="{now.isoformat()}Z" start="{now.isoformat()}Z"
       stale="{stale.isoformat()}Z" how="m-g">
  <point lat="{lat}" lon="{lon}" hae="0" ce="5" le="5"/>
  <detail>
    <contact callsign="{contact_callsign}"/>
    <remarks>Test point from Python</remarks>
  </detail>
</event>'''
    return cot_xml

def xy_to_latlon(x, y):
    """
    Convert relative x/y offsets in meters from the origin to lat/lon.
    
    x: meters east from origin
    y: meters north from origin
    """
    lon, lat = transformer.transform(x, y)
    return lat, lon