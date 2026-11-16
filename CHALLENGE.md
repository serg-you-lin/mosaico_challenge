# Mission YB-42

Last night, spot-07 ran a patrol of Yard B. The log is in `spot_yb42.mcap` (ROS 2, ~13 MB, 87 s):
IMU, joint states, odometry, tf, four foot load cells, a front camera, battery and the mission log.

The night-shift operator swears nothing happened.

1. Ingest the recording into Mosaico:
   ```bash
   mosaicolabs.ros_injector spot_yb42.mcap --name spot_yb42 --metadata sequence_metadata.json
   ```
2. With a **single Mosaico query**, find the moment spot-07 was in **free fall**. That's when its IMU measured almost no vertical acceleration.
3. Send us the exact start timestamp of that window (UTC, nanoseconds), plus the query you used.

Bonus: once you know *when*, take a look at *what* the robot saw, and *where* it walked.


FROM DISCORD CHANNEL

🤖  Physical Education: vol. 1 — Selection Challenge
Welcome! This is where you get your spot at the Mosaico hackathon on robotics and physical AI.  📍 Albert School, Milan · 📅 27–29 November  ━━━━━━━━━━━━━━━━━━━━  
How it works
1. Read the challenge below and download the file attached to this message. 
💡 The challenge is optional, but highly recommended: it's the best way to show us what you can do. If you skip it, we'll evaluate your application based on your GitHub, background and LinkedIn profile. 

2. Set up Mosaico — https://github.com/mosaico-labs/mosaico · https://docs.mosaico.dev/  3. Submit your answer here: https://forms.gle/jZz8TRyANJi1GWSN7 ⚠️ Use the same email you registered with on Luma.  ⏰ Deadline: 19 November  ━━━━━━━━━━━━━━━━━━━━  
The challenge
Mission YB-42 Last night, spot-07 ran a patrol of Yard B. The log is in spot_yb42.mcap (ROS 2, ~13 MB, 87 s): IMU, joint states, odometry, tf, four foot load cells, a front camera, battery and the mission log.  The night-shift operator swears nothing happened.  1. Ingest the recording into Mosaico: 

mosaicolabs.ros_injector spot_yb42.mcap --name spot_yb42 --metadata sequence_metadata.json

2. With a single Mosaico query, find the moment spot-07 was in free fall. That's when its IMU measured almost no vertical acceleration.  3. Send us the exact start timestamp of that window (UTC, nanoseconds), plus the query you used.  Bonus: once you know when, take a look at what the robot saw, and where it walked.  ━━━━━━━━━━━━━━━━━━━━  
Questions?
Ask right here in this channel, we're happy to help. For anything else: hackathon@mosaico.dev  🚫 Please don't post your answer here. Submit it only through the form, so everyone gets a fair shot. 

