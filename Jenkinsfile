pipeline {
    agent {
        docker { 
            image 'python:3.14-alpine'
            args '--user root -v /var/run/docker.sock:/var/run/docker.sock' // mount Docker socket to access the host's Docker daemon
        }
    }
    stages {
        stage('Checkout') {
            steps {
                sh 'echo passed'
                //git branch: 'main', url: 'https://github.com/devops-timi/cicd-focusflow-deploy.git'
            }
        }

        stage('Initialize') {
            steps {
                // Install docker-cli so this agent can talk to the host daemon
                sh 'apk add --no-cache docker-cli'
            }
        }
        stage('Install Dependencies') {
            steps {
                sh '''
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest
                '''
            }
        }

        stage('Test App') {
            steps {
                echo 'Running Pytest...'
                sh '''
                    python3 -m pytest tests/test_app.py
                '''
            }
        }  

        stage('Build and Push Docker Image') {
            environment {
                DOCKER_IMAGE = "devopstimi/focusflow-cicd:${BUILD_NUMBER}"
                // DOCKERFILE_LOCATION = "Dockerfile"
                REGISTRY_CREDENTIALS = credentials('docker-cred')
            }
            steps {
                script {
                    sh "docker build -t ${DOCKER_IMAGE} ."
                    def dockerImage = docker.image("${DOCKER_IMAGE}")
                    docker.withRegistry('https://index.docker.io/v1/', "docker-cred") {
                        dockerImage.push()
                    }
                }
            }
        }

        stage('Update Deployment File') {
            environment {
                GIT_REPO_NAME = "cicd-focusflow-deploy"
                GIT_USER_NAME = "devops-timi"
            }
            steps {
                withCredentials([string(credentialsId: 'github', variable: 'GITHUB_TOKEN')]) {
                    sh """
                        git config user.email "tobalereko@gmail.com"
                        git config user.name "Timilehin Obalereko"
                        BUILD_NUMBER=${BUILD_NUMBER}
                        sed -i "s/replaceImageTag/${BUILD_NUMBER}/g" deploy/deployment.yml
                        git add deploy/deployment.yml
                        git commit -m "Update deployment image to version ${BUILD_NUMBER}"
                        git push https://${GITHUB_TOKEN}@github.com/${GIT_USER_NAME}/${GIT_REPO_NAME} HEAD:main
                    """
                }
            }
        }
    }
}