SELECT 
	shipment_id, 
	SUM(plan1) AS planned,
	SUM(add1) AS added, 
	SUM(miss1) AS miss,
	SUM(equal1) AS equal
FROM(	
   SELECT 
	/*p.shipment_id, n.shipment_id AS n_ship_id,
	p.id as pid,
	n.id as nid, n.asset_id as nd_assid , 
	m.id as mo_id, m.asset_id as mo_assid, 
	
	CASE WHEN n.asset_id IS NOT NULL THEN n.asset_id ELSE m.asset_id END AS id,
	*/
	CASE WHEN p.shipment_id IS NOT NULL THEN p.shipment_id ELSE n.shipment_id END AS shipment_id,
	CASE WHEN n.asset_id IS NOT NULL THEN n.asset_id ELSE m.asset_id END AS asset_id,
	--a.name, 
	/*CASE 
		WHEN n.id IS NULL AND m.id IS NOT NULL THEN 'added' 
		WHEN n.id IS NOT NULL AND m.id IS NULL THEN 'miss' 
		WHEN n.id IS NOT NULL AND m.state = 'unreceived' THEN 'miss' 
		WHEN n.id IS NOT NULL AND m.state != 'unreceived' THEN 'equal' 
		ELSE 'unknown' END
		AS state,
	*/	
	CASE WHEN n.id IS NOT NULL THEN 1 ELSE 0 END AS plan1,
	CASE WHEN n.id IS NULL AND m.id IS NOT NULL THEN 1 ELSE 0 END AS add1,
	CASE WHEN n.id IS NOT NULL AND (m.id IS NULL OR m.state = 'unreceived') THEN 1 ELSE 0 END AS miss1,
	CASE WHEN n.id IS NOT NULL AND m.state != 'unreceived' THEN 1 ELSE 0 END AS equal1
		
	--,m.state as mstate
	

	-- SELECT *
FROM

(	-- #get party.id by latest date
	SELECT DISTINCT ON (shipment_id)
	       id,shipment_id --,date
	FROM   asset_move_party
	WHERE shipment_id IN (1,2) --IS NOT NULL --IN (1,2)
	ORDER  BY shipment_id, "date" DESC
)p

LEFT JOIN asset_move m ON 
	m.party_id = p.id 
	
FULL OUTER JOIN asset_shipment_planned n ON n.shipment_id = p.shipment_id	
	AND 
	m.asset_id = n.asset_id

--LEFT JOIN asset_asset a ON a.id = m.asset_id OR a.id = n.asset_id
-- WHERE n.shipment_id IS NOT NULL
--ORDER BY n.shipment_id, n.id, p.id, m.id --, a.id
) a
GROUP BY shipment_id