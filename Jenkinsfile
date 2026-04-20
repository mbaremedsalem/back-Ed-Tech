pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'ed-tech-image'
        CONTAINER_NAME = 'ed-tech-container'
        DOCKER_HUB_REPO = 'mbaremedsalem/back-ed-tech'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📦 Récupération du code depuis GitHub...'
                checkout scm
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo '🐳 Construction de l\'image Docker...'
                sh 'docker build -t $DOCKER_IMAGE .'
            }
        }
        
        stage('Test Container') {
            steps {
                echo '🧪 Test du conteneur...'
                sh '''
                    docker stop $CONTAINER_NAME || true
                    docker rm $CONTAINER_NAME || true
                    docker run -d -p 8000:8000 --name $CONTAINER_NAME $DOCKER_IMAGE
                    sleep 5
                    curl --fail http://localhost:8000 || exit 1
                    echo "✅ Conteneur fonctionne correctement"
                '''
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                echo '📤 Push de l\'image vers Docker Hub...'
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker tag $DOCKER_IMAGE $DOCKER_HUB_REPO:latest
                        docker push $DOCKER_HUB_REPO:latest
                    '''
                }
            }
        }
        
        stage('Deploy to DigitalOcean') {
            steps {
                echo 'Déploiement sur DigitalOcean...'
                sh '''
                    ssh -o StrictHostKeyChecking=no root@VOTRE_IP_DIGITALOCEAN << 'EOF'
                        echo "Pull de la nouvelle image..."
                        docker pull $DOCKER_HUB_REPO:latest
                        
                        echo "Arrêt de l'ancien conteneur..."
                        docker stop back-ed-tech || true
                        docker rm back-ed-tech || true
                        
                        echo "Démarrage du nouveau conteneur..."
                        docker run -d -p 80:8000 --name back-ed-tech $DOCKER_HUB_REPO:latest
                        
                        echo "Déploiement terminé !"
                    EOF
                '''
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline réussi ! Application déployée avec succès.'
        }
        failure {
            echo 'Pipeline échoué. Consultez les logs pour plus de détails.'
        }
    }
}