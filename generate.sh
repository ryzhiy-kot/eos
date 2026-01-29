echo "#!/bin/bash
base64 -d << 'EOF' | tar -xz
\$(tar -czf - . | base64)
EOF" > restore.sh && chmod +x restore.sh

# ./restore.sh