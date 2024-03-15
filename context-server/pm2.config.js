module.exports = {
  apps: [
    {
      name: 'isim-main',
      script: 'start-server.py',
      interpreter: 'python3',
      watch: true,
      min_uptime: 5000,
      max_restarts: 3,
    },
  ],
};
