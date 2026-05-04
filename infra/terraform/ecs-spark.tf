resource "aws_ecs_task_definition" "spark" {
  family                   = "${local.name_prefix}-spark-job"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "spark_job"
      image     = "${data.aws_ecr_repository.repos["spark_job"].repository_url}:${var.image_tag}"
      essential = true
      environment = [
        {
          name  = "SPARK_JDBC_URL"
          value = "jdbc:postgresql://${aws_db_instance.postgres.address}:5432/iot_db"
        },
        {
          name  = "DB_USER"
          value = var.db_username
        },
        {
          name  = "DB_PASS"
          value = var.db_password
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app["spark_job"].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-spark-task"
  })
}

resource "aws_cloudwatch_event_rule" "spark_schedule" {
  name                = "${local.name_prefix}-spark-schedule"
  description         = "Scheduled Spark batch processing trigger."
  schedule_expression = var.spark_schedule_expression

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-spark-schedule"
  })
}

resource "aws_cloudwatch_event_target" "spark_ecs_target" {
  rule      = aws_cloudwatch_event_rule.spark_schedule.name
  target_id = "spark-fargate-task"
  arn       = aws_ecs_cluster.main.arn
  role_arn  = aws_iam_role.eventbridge_ecs.arn

  ecs_target {
    launch_type         = "FARGATE"
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.spark.arn
    platform_version    = "LATEST"

    network_configuration {
      subnets          = [for subnet in aws_subnet.private : subnet.id]
      security_groups  = [aws_security_group.ecs_tasks.id]
      assign_public_ip = false
    }
  }
}
