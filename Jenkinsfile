pipeline {
  agent any
    stages {
      stage('Lint') {
        agent {
            docker {
                image 'python:3.11.3-buster'
                args '-u 0'
            }
        }
        when {
          anyOf {
            branch pattern: "feature*"
            branch pattern: "fix*"
            branch pattern: "feaute-ci"
          }
        }
        steps {
          sh "pip install poetry"
          sh "poetry install --with dev"
          sh "poetry run -- black --check *.py"
        }
      }
      stage('Build') {
      when {
        anyOf {
          branch pattern: "feaute-ci"
        }
      }
      steps {
        script {
          def image = docker.build "freeko/bank_app:${env.GIT_COMMIT}"
          docker.withRegistry('','freeko_dockerhub') {
            image.push()
          }
        }
      }
    }
  }
}