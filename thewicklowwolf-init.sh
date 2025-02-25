#!/bin/sh

# echo -e "\033[1;32mTheWicklowWolf\033[0m"
echo -e "\033[1;34mSpotTube\033[0m"
echo "Initializing app..."

cat << 'EOF'
_____________________________________

               .-'''''-.             
             .'         `.           
            :             :          
           :               :         
           :      _/|      :         
            :   =/_/      :          
             `._/ |     .'           
          (   /  ,|...-'             
           \_/^\/||__                
       _/~  `""~`"` \_               
     __/  -'/  `-._ `\_\__           
    /    /-'`  `\   \  \-.\          
_____________________________________
Initially created by TheWicklowWolf   
Forked by jyyyeung
_____________________________________

EOF

echo "-----------------"
echo -e "\033[1mInstalled Versions\033[0m"
# Get the version of yt-dlp
echo -n "yt-dlp: "
pip show yt-dlp | grep Version: | awk '{print $2}'

# Get the version of ffmpeg
echo -n "FFmpeg: "
ffmpeg -version | head -n 1 | awk '{print $3}'
echo "-----------------"

PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "-----------------"
echo -e "\033[1mRunning with:\033[0m"
echo "PUID=${PUID}"
echo "PGID=${PGID}"
echo "-----------------"

# Create the required directories with the correct permissions
echo "Setting up directories.."
mkdir -p /app/downloads /app/config /app/cache /app/instance
chown -R ${PUID}:${PGID} /app

# Set XDG_CACHE_HOME to use the cache directory
export XDG_CACHE_HOME=/app/cache

# Copy the example environment file to the instance directory
echo "Copying example environment file to the instance directory..."
if [ ! -f /app/.env ]; then
    cp .env.example /app/.env
fi

# Start the application with the specified user permissions
echo "Running SpotTube $RELEASE_VERSION..."
exec su-exec ${PUID}:${PGID} gunicorn src.SpotTube:app -c gunicorn_config.py
