=======================================================================
=                       redis has been installed                      =
=======================================================================

# Redis can be accessed via port 6379 on the following DNS names from within your cluster:

# redis-master.redis.svc.cluster.local for read/write operations
# redis-slave.redis.svc.cluster.local for read-only operations


# To get your password run:

  export REDIS_PASSWORD=$(kubectl get secret --namespace redis redis -o jsonpath="{.data.redis-password}" | base64 --decode)

# To connect to your Redis server:

# 1. Run a Redis pod that you can use as a client:

  kubectl run --namespace redis redis-client --rm --tty -i --restart='Never' \
   --env REDIS_PASSWORD=$REDIS_PASSWORD \
   --image docker.io/bitnami/redis:5.0.7-debian-10-r48 -- bash

# 2. Connect using the Redis CLI:
  redis-cli -h redis-master -a $REDIS_PASSWORD
  redis-cli -h redis-slave -a $REDIS_PASSWORD

# To connect to your database from outside the cluster execute the following commands:

  kubectl port-forward --namespace redis svc/redis-master 6379:6379 &
  redis-cli -h 127.0.0.1 -p 6379 -a $REDIS_PASSWORD
