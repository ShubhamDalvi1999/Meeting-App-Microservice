.\scripts\Set-Environment.ps1 -Environment development

Minikube Development:
1.Start Minikube:
   -minikube start
2.Enable Minikube addons:
   -minikube addons enable ingress

kubectl apply -f k8s/config/development/


docker build -t meeting-app-backend:dev -f backend/flask-service/Dockerfile ./backend/flask-service

docker build -t meeting-app-frontend:dev -f frontend/Dockerfile ./frontend

kubectl apply -f k8s/config/development/configmap.yaml

kubectl apply -f k8s/config/development/secrets.yaml

kubectl apply -f k8s/config/development/deployment.yaml

kubectl get services

kubectl get pods


$env:Path += ';C:\Program Files\Kubernetes\Minikube'

minikube docker-env

docker build -t meeting-app-backend:dev ./backend/flask-service
docker build -t meeting-app-frontend:dev ./frontend

F:\Full Stack Meeting App>minikube image load meeting-app-frontend:dev
W1228 23:48:37.412888  112092 main.go:291] Unable to resolve the current Docker CLI context "default": context "default": context not found: open C:\Users\ASUS\.docker\contexts\meta\37a8eec1ce19687d132fe29051dca629d164e2c4958ba141d5f4133a33f0688f\meta.json: The system cannot find the path specified.

minikube -p minikube docker-env | Invoke-Expression

First, let's stop and start Minikube with the Docker driver:

	nikube stop; minikube start --driver=docker --mount-string="F:/Full Stack Meeting App:/app" --mount

Now let's set up the Docker environment and rebuild the images:

$env:DOCKER_HOST="tcp://127.0.0.1:2375"; docker build -t meeting-app-frontend:dev ./frontend

minikube docker-env


Let's try a different approach. Since we're on Windows with Docker Desktop, let's use Docker Desktop's Kubernetes instead:
Switch to Docker Desktop's Kubernetes:

kubectl config get-contexts

I see we're still on Minikube. Let's try one last approach with Minikube:
Enable the registry addon in Minikube:

minikube addons enable registry


Now let's update our frontend deployment to use the Minikube registry


docker tag meeting-app-frontend:dev localhost:51931/meeting-app-frontend:dev; docker push localhost:51931/meeting-app-frontend:dev

minikube stop
-----------------------------------------------------------------------

minikube start --driver=docker --memory=4096 --cpus=2

minikube docker-env | Out-String

$Env:DOCKER_TLS_VERIFY = "1"; $Env:DOCKER_HOST = "tcp://127.0.0.1:52247"; $Env:DOCKER_CERT_PATH = "C:\Users\ASUS\.minikube\certs"; $Env:MINIKUBE_ACTIVE_DOCKERD = "minikube"

docker build -t meeting-app-frontend:dev ./frontend

docker build -t meeting-app-backend:dev ./backend/flask-service

kubectl apply -f k8s/config/development/

kubectl get pods

kubectl get pods --all-namespaces

Backend  docker was not coneected to database:
kubectl apply -f k8s/config/development/configmap.yaml; kubectl rollout restart deployment meeting-app


The Flask migrations are not properly initialized. Let's modify the backend deployment to skip migrations on startup for now:
docker build -t meeting-app-backend:dev ./backend/flask-service
minikube image load meeting-app-backend:dev

$env:Path += ";C:\Program Files\Kubernetes\Minikube"

minikube image load meeting-app-backend:dev


Let's check the ConfigMap and make sure all the necessary environment variables are set:
kubectl get configmap meeting-app-config -o yaml


every Kubernetes pod was up and running but i was not able to see local host :
minikube service list
kubectl port-forward service/meeting-app-frontend 30000:3000
Let's update the Next.js configuration to explicitly allow connections from all hosts:
changed the code 

docker build -t meeting-app-frontend:dev ./frontend

kubectl apply -f k8s/config/development/frontend-deployment.yaml

-------------------------------------------------------------------------------
minikube status

PS F:\Full Stack Meeting App> minikube status
E1229 00:42:13.210984  123204 status.go:417] kubeconfig endpoint: got: 127.0.0.1:56841, want: 127.0
.0.1:60923
minikube
type: Control Plane
host: Running
kubelet: Stopped
apiserver: Stopped
kubeconfig: Misconfigured
docker-env: in-use


WARNING: Your kubectl is pointing to stale minikube-vm.
To fix the kubectl context, run `minikube update-context`

Let's fix the Minikube context and restart the services:
Update the Minikube context:

minikube update-context

PS F:\Full Stack Meeting App> minikube update-context
💗  Current context is "minikube"
PS F:\Full Stack Meeting App>
3

minikube start --driver=docker --ports=30000:30000,30963:30963,30283:30283

& minikube -p minikube docker-env | Invoke-Expression


docker build -t meeting-app-frontend:dev ./frontend

docker build -t meeting-app-backend:dev ./backend/flask-service

kubectl apply -f k8s/config/development/


kubectl get pods
It seems the pods haven't been created yet. Let's restart the deployments:
kubectl rollout restart deployment meeting-app meeting-app-frontend postgres redis

kubectl get pods