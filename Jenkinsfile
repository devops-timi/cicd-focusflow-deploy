pipeline {
    
    agent any

    stages {

        stage('Test App') {
            agent {
                docker { 
                    image 'python:3.12-alpine'
                    args '-u 0'
                }
            }
            steps {
                echo 'Running Pytest...'
                sh '''
                    pip install -r requirements.txt
                    python3 -m pytest tests/test_app.py
                '''
            }
        }  

        stage('Build and Push Docker Image') {
            agent any
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
                        sh "docker push ${DOCKER_IMAGE}"
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
                    sh '''
                        git config --global user.email "tobalereko@gmail.com"
                        git config --global user.name "Timilehin Obalereko"
                        
                        # Clone the repo fresh
                        rm -rf temp_repo
                        git clone https://${GITHUB_TOKEN}@github.com/${GIT_USER_NAME}/${GIT_REPO_NAME}.git temp_repo
                        cd temp_repo
                        
                        # Make the changes
                        sed -i "s/replaceImageTag/${BUILD_NUMBER}/g" deploy/deployment.yml
                        
                        # Commit and push
                        git add deploy/deployment.yml
                        git commit -m "Update deployment image to version ${BUILD_NUMBER}"
                        git push origin main
                        
                        # Clean up
                        cd ..
                        rm -rf temp_repo
                    '''
                }
            }
        }
    }
}