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
          branch pattern: "master"
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
    stage('Update Helm Chart') {
      when {
        branch "master"
       }
      steps {
        sh "git config --global pull.rebase true"
        sh "git pull origin feature-CD"
        sh "git branch"
        sh "git checkout feature-CD"
        script {
        def filename = 'k8s/bank/values-prd.yaml'
        def data = readYaml file: filename

        // Change something in the file
        data.image.tag = "${env.GIT_COMMIT}"

        sh "rm $filename"
        writeYaml file: filename, data: data

          withCredentials([string(credentialsId: 'freeko_github_token', variable: 'SECRET')]) {
                sh('git config --global user.email "dmitrii.baturevich@diginetica.com" && git config --global user.name "Jenkins"')
                sh('git add $filename')
                sh('git commit -m "JENKINS: add new image tag for CD"')
                sh('git remote set-url origin https://${SECRET}@github.com/Freek0/dos14-baturevich_dmitry-git-flow')
                sh('git push origin feature-CD')
          }
        }
      }
    }
  }
}