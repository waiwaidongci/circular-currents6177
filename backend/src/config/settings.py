import os
DATABASE_URL=os.getenv('DATABASE_URL','mysql+pymysql://currents:currents_demo_2026@localhost:17729/circular_currents')
REDIS_URL=os.getenv('REDIS_URL','redis://localhost:6379/0')
JWT_SECRET=os.getenv('JWT_SECRET','jijia-local-demo-change-for-deployment')
