locals {
  db_password_urlencoded = urlencode(var.db_password)

  database_urls = {
    for db_name in local.database_names :
    db_name => "postgresql://${var.db_username}:${local.db_password_urlencoded}@${aws_db_instance.postgres.address}:5432/${db_name}"
  }

  redis_url = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0"

  app_log_groups = toset(concat(keys(local.backend_services), ["frontend", "api_gateway", "db_seeder", "spark_job"]))
}

resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-ecs-cluster"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ecs-cluster"
  })
}

resource "aws_cloudwatch_log_group" "app" {
  for_each = local.app_log_groups

  name              = "/ecs/${local.name_prefix}/${each.value}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-${each.value}-logs"
  })
}

resource "aws_service_discovery_private_dns_namespace" "apps" {
  name = var.service_discovery_namespace
  vpc  = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-service-discovery"
  })
}

resource "aws_service_discovery_service" "backend" {
  for_each = local.backend_services

  name = each.key

  dns_config {
    namespace_id   = aws_service_discovery_private_dns_namespace.apps.id
    routing_policy = "MULTIVALUE"

    dns_records {
      ttl  = 10
      type = "A"
    }
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

resource "aws_ecs_task_definition" "backend" {
  for_each = local.backend_services

  family                   = "${local.name_prefix}-${each.key}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.microservice_cpu)
  memory                   = tostring(var.microservice_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = each.key
      image     = "${data.aws_ecr_repository.repos[each.value.repository_name].repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 5000
          hostPort      = 5000
          protocol      = "tcp"
        }
      ]
      environment = concat(
        [
          {
            name  = each.value.database_env_var
            value = local.database_urls[each.value.database_name]
          },
          {
            name  = "JWT_SECRET_KEY"
            value = var.jwt_secret_key
          },
          {
            name  = "INTERNAL_SERVICE_TOKEN"
            value = var.internal_service_token
          }
        ],
        each.key == "supplier_service" ? [
          {
            name  = "REDIS_URL"
            value = local.redis_url
          }
        ] : [],
        each.key == "booking_service" ? [
          {
            name  = "STRIPE_SECRET_KEY"
            value = var.stripe_secret_key
          }
        ] : [],
        [
          for env_name, env_value in each.value.extra_env : {
            name  = env_name
            value = env_value
          }
        ]
      )
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app[each.key].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-${each.key}-task"
  })
}

resource "aws_ecs_service" "backend" {
  for_each = local.backend_services

  name            = "${local.name_prefix}-${each.key}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend[each.key].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = [for subnet in aws_subnet.private : subnet.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.backend[each.key].arn
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-${each.key}-service"
  })
}

resource "aws_ecs_task_definition" "api_gateway" {
  family                   = "${local.name_prefix}-api-gateway"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.microservice_cpu)
  memory                   = tostring(var.microservice_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "api_gateway"
      image     = "${data.aws_ecr_repository.repos["api_gateway"].repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "AUTH_SERVICE_HOST"
          value = "auth_service.${var.service_discovery_namespace}"
        },
        {
          name  = "SUPPLIER_SERVICE_HOST"
          value = "supplier_service.${var.service_discovery_namespace}"
        },
        {
          name  = "BOOKING_SERVICE_HOST"
          value = "booking_service.${var.service_discovery_namespace}"
        },
        {
          name  = "GAMIFICATION_SERVICE_HOST"
          value = "gamification_service.${var.service_discovery_namespace}"
        },
        {
          name  = "IOT_ANALYTICS_SERVICE_HOST"
          value = "iot_analytics_service.${var.service_discovery_namespace}"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app["api_gateway"].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-api-gateway-task"
  })
}

resource "aws_ecs_service" "api_gateway" {
  name            = "${local.name_prefix}-api-gateway"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api_gateway.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = [for subnet in aws_subnet.private : subnet.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api_gateway.arn
    container_name   = "api_gateway"
    container_port   = 80
  }

  depends_on = [aws_lb_listener_rule.api_paths]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-api-gateway-service"
  })
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.microservice_cpu)
  memory                   = tostring(var.microservice_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${data.aws_ecr_repository.repos["frontend"].repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app["frontend"].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-task"
  })
}

resource "aws_ecs_task_definition" "db_seeder" {
  family                   = "${local.name_prefix}-db-seeder"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "db_seeder"
      image     = "${data.aws_ecr_repository.repos["db_seeder"].repository_url}:${var.image_tag}"
      essential = true
      command   = ["python", "populate_db.py"]
      environment = [
        {
          name  = "AUTH_DATABASE_URL"
          value = local.database_urls["auth_db"]
        },
        {
          name  = "SUPPLIER_DATABASE_URL"
          value = local.database_urls["supplier_db"]
        },
        {
          name  = "BOOKING_DATABASE_URL"
          value = local.database_urls["booking_db"]
        },
        {
          name  = "GAMIFICATION_DATABASE_URL"
          value = local.database_urls["gamification_db"]
        },
        {
          name  = "IOT_DATABASE_URL"
          value = local.database_urls["iot_db"]
        },
        {
          name  = "REDIS_URL"
          value = local.redis_url
        },
        {
          name  = "JWT_SECRET_KEY"
          value = var.jwt_secret_key
        },
        {
          name  = "INTERNAL_SERVICE_TOKEN"
          value = var.internal_service_token
        },
        {
          name  = "STRIPE_SECRET_KEY"
          value = var.stripe_secret_key
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app["db_seeder"].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-db-seeder-task"
  })
}

resource "aws_ecs_service" "frontend" {
  name            = "${local.name_prefix}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = [for subnet in aws_subnet.private : subnet.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.http]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-service"
  })
}
