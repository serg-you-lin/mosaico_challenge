"""freefall_query.py — query unica Mosaico: finestre in cui l'IMU misura
accelerazione verticale quasi nulla (caduta libera)."""

from mosaicolabs import IMU, MosaicoClient, QueryOntologyCatalog

# Soglia in m/s^2: a riposo az ~ 9.81, in caduta libera ~ 0
THRESHOLD = 1.0

query = QueryOntologyCatalog(IMU.Q.acceleration.z.between([-THRESHOLD, THRESHOLD]))

with MosaicoClient.connect("localhost", 6726) as client:
    results = client.query(query)
    for item in results:
        print(f"Sequence: {item.sequence.name}")
        for topic in item.topics:
            # I campi della risposta cambiano tra versioni dell'SDK: li stampo tutti
            print(f"  Topic: {topic.name}  fields: {vars(topic)}")
            for cluster in topic.clusterize():
                start, end = cluster.timerange.start, cluster.timerange.end
                print(f"    window start={start} ns  end={end} ns  "
                      f"durata={(end - start) / 1e9:.3f} s")
