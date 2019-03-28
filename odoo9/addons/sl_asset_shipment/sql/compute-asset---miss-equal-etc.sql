--SELECT pid, shipment_id, sum(plan1) AS plan, sum(add1) as added, sum(miss1) as missing, sum(receive1) as received FROM (
-- INFO: +fields: asset Total, miss, equal, added
SELECT 	n.id as nid, m.id as mo_id, 
	n.asset_id as nd_assid, m.asset_id as mo_assid, m.state,
	
	p.id as pid, p.shipment_id,
	CASE WHEN n.id IS NOT NULL THEN 1 ELSE 0 END AS plan1,
	CASE WHEN n.id IS NULL AND m.id IS NOT NULL THEN 1 ELSE 0 END AS add1,
	CASE WHEN n.id IS NOT NULL AND (m.id IS NULL OR m.state = 'unreceived') THEN 1 ELSE 0 END AS miss1,
	CASE WHEN n.id IS NOT NULL AND m.state != 'unreceived' THEN 1 ELSE 0 END AS receive1
	

FROM asset_move_party p
FULL OUTER JOIN asset_move m ON 
	m.party_id = p.id 
FULL OUTER JOIN asset_shipment_planned n ON n.shipment_id = p.shipment_id	
	AND (m.asset_id = n.asset_id OR m.id IS NULL)

WHERE p.id in (7,11)--,8,9,10,11) --%s
--)A GROUP BY pid,shipment_id