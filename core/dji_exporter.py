import os
import time
import zipfile
from xml.sax.saxutils import escape

MAX_WAYPOINTS_PER_KMZ = 200
WPML_NS = "http://www.dji.com/wpmz/1.0.6"


def _mission_config(speed, include_payload=False):
    payload = """
      <wpml:payloadInfo>
        <wpml:payloadEnumValue>53</wpml:payloadEnumValue>
        <wpml:payloadSubEnumValue>0</wpml:payloadSubEnumValue>
        <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
      </wpml:payloadInfo>""" if include_payload else ""
    return f"""<wpml:missionConfig>
      <wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode>
      <wpml:finishAction>goHome</wpml:finishAction>
      <wpml:exitOnRCLost>executeLostAction</wpml:exitOnRCLost>
      <wpml:executeRCLostAction>goBack</wpml:executeRCLostAction>
      <wpml:takeOffSecurityHeight>20</wpml:takeOffSecurityHeight>
      <wpml:globalTransitionalSpeed>{speed:.1f}</wpml:globalTransitionalSpeed>
      <wpml:droneInfo>
        <wpml:droneEnumValue>67</wpml:droneEnumValue>
        <wpml:droneSubEnumValue>0</wpml:droneSubEnumValue>
      </wpml:droneInfo>{payload}
    </wpml:missionConfig>"""


def build_template(global_height, speed):
    ts = int(time.time() * 1000)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="{WPML_NS}">
  <Document>
    <wpml:author>GeoFly QGIS</wpml:author>
    <wpml:createTime>{ts}</wpml:createTime>
    <wpml:updateTime>{ts}</wpml:updateTime>
    {_mission_config(speed, include_payload=False)}
    <Folder>
      <wpml:templateType>waypoint</wpml:templateType>
      <wpml:templateId>0</wpml:templateId>
      <wpml:globalHeight>{global_height:.2f}</wpml:globalHeight>
      <wpml:executeHeightMode>relativeToStartPoint</wpml:executeHeightMode>
      <wpml:waylineCoordinateSysParam>
        <wpml:coordinateMode>WGS84</wpml:coordinateMode>
        <wpml:heightMode>relativeToStartPoint</wpml:heightMode>
      </wpml:waylineCoordinateSysParam>
      <wpml:autoFlightSpeed>{speed:.1f}</wpml:autoFlightSpeed>
      <wpml:gimbalPitchMode>manual</wpml:gimbalPitchMode>
      <wpml:globalWaypointTurnMode>coordinateTurn</wpml:globalWaypointTurnMode>
      <wpml:globalUseStraightLine>1</wpml:globalUseStraightLine>
    </Folder>
  </Document>
</kml>'''


def _action_group(idx, photo, first, gimbal_pitch):
    actions = []
    action_id = 0
    if first:
        actions.append(f'''          <wpml:action>
            <wpml:actionId>{action_id}</wpml:actionId>
            <wpml:actionActuatorFunc>gimbalRotate</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:gimbalHeadingYawBase>aircraft</wpml:gimbalHeadingYawBase>
              <wpml:gimbalRotateMode>absoluteAngle</wpml:gimbalRotateMode>
              <wpml:gimbalPitchRotateEnable>1</wpml:gimbalPitchRotateEnable>
              <wpml:gimbalPitchRotateAngle>{int(gimbal_pitch)}</wpml:gimbalPitchRotateAngle>
              <wpml:gimbalRollRotateEnable>0</wpml:gimbalRollRotateEnable>
              <wpml:gimbalRollRotateAngle>0</wpml:gimbalRollRotateAngle>
              <wpml:gimbalYawRotateEnable>0</wpml:gimbalYawRotateEnable>
              <wpml:gimbalYawRotateAngle>0</wpml:gimbalYawRotateAngle>
              <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
            </wpml:actionActuatorFuncParam>
          </wpml:action>''')
        action_id += 1
        actions.append(f'''          <wpml:action>
            <wpml:actionId>{action_id}</wpml:actionId>
            <wpml:actionActuatorFunc>hover</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:hoverTime>2.5</wpml:hoverTime>
            </wpml:actionActuatorFuncParam>
          </wpml:action>''')
        action_id += 1
    if photo:
        actions.append(f'''          <wpml:action>
            <wpml:actionId>{action_id}</wpml:actionId>
            <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
            </wpml:actionActuatorFuncParam>
          </wpml:action>''')
    if not actions:
        return ""
    joined = "\n".join(actions)
    return f'''        <wpml:actionGroup>
          <wpml:actionGroupId>{idx}</wpml:actionGroupId>
          <wpml:actionGroupStartIndex>{idx}</wpml:actionGroupStartIndex>
          <wpml:actionGroupEndIndex>{idx}</wpml:actionGroupEndIndex>
          <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
          <wpml:actionTrigger>
            <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
          </wpml:actionTrigger>
{joined}
        </wpml:actionGroup>'''


def build_waylines(waypoints_wgs84, speed, gimbal_pitch):
    placemarks = []
    for idx, wp in enumerate(waypoints_wgs84):
        action_group = _action_group(idx, bool(wp.get("photo")), idx == 0, gimbal_pitch)
        if action_group:
            action_group = "\n" + action_group
        placemarks.append(f'''      <Placemark>
        <wpml:index>{idx}</wpml:index>
        <Point>
          <coordinates>{wp["lon"]:.8f},{wp["lat"]:.8f},0</coordinates>
        </Point>
        <wpml:executeHeight>{wp["execute_h"]:.2f}</wpml:executeHeight>
        <wpml:waypointSpeed>{speed:.1f}</wpml:waypointSpeed>
        <wpml:waypointHeadingParam>
          <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>
          <wpml:waypointHeadingAngle>0</wpml:waypointHeadingAngle>
        </wpml:waypointHeadingParam>
        <wpml:waypointTurnParam>
          <wpml:waypointTurnMode>coordinateTurn</wpml:waypointTurnMode>
          <wpml:waypointTurnDampingDist>0.2</wpml:waypointTurnDampingDist>
        </wpml:waypointTurnParam>{action_group}
      </Placemark>''')
    body = "\n".join(placemarks)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="{WPML_NS}">
  <Document>
    {_mission_config(speed, include_payload=True)}
    <Folder>
      <wpml:templateId>0</wpml:templateId>
      <wpml:executeHeightMode>relativeToStartPoint</wpml:executeHeightMode>
      <wpml:waylineId>0</wpml:waylineId>
      <wpml:autoFlightSpeed>{speed:.1f}</wpml:autoFlightSpeed>
{body}
    </Folder>
  </Document>
</kml>'''


def validate_waypoints(waypoints):
    if not waypoints:
        raise ValueError("Não há waypoints para exportar.")
    for i, wp in enumerate(waypoints):
        for key in ("lat", "lon", "execute_h"):
            val = wp.get(key)
            if val is None:
                raise ValueError(f"Waypoint {i}: campo {key} ausente.")
            if val != val or val in (float("inf"), float("-inf")):
                raise ValueError(f"Waypoint {i}: campo {key} inválido.")
        if not (-90 <= wp["lat"] <= 90 and -180 <= wp["lon"] <= 180):
            raise ValueError(f"Waypoint {i}: coordenadas inválidas.")
        if wp["execute_h"] < 2:
            raise ValueError(f"Waypoint {i}: executeHeight abaixo de 2 m.")


def export_kmz(output_path, waypoints_wgs84, global_height, speed, gimbal_pitch=-90):
    validate_waypoints(waypoints_wgs84)
    chunks = [waypoints_wgs84[i:i + MAX_WAYPOINTS_PER_KMZ]
              for i in range(0, len(waypoints_wgs84), MAX_WAYPOINTS_PER_KMZ)]
    outputs = []
    base, ext = os.path.splitext(output_path)
    if ext.lower() != ".kmz":
        base = output_path
    for part_idx, chunk in enumerate(chunks, start=1):
        path = f"{base}_parte_{part_idx:02d}.kmz" if len(chunks) > 1 else f"{base}.kmz"
        template = build_template(global_height, speed)
        waylines = build_waylines(chunk, speed, gimbal_pitch)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("template.kml", template.encode("utf-8"))
            z.writestr("waylines.wpml", waylines.encode("utf-8"))
        outputs.append(path)
    return outputs
