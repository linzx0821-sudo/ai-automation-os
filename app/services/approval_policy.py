from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    required: bool
    reason: str | None = None


class ApprovalPolicy:
    """Conservative V0.1 preflight policy for high-impact user goals.

    This policy is intentionally deterministic and auditable. It is not an LLM
    classifier. Domain workflows may add more precise approval checks later.
    """

    _HIGH_IMPACT_PHRASES = (
        "deploy to production",
        "production deploy",
        "delete production",
        "delete database",
        "drop database",
        "send email",
        "send message",
        "publish publicly",
        "place order",
        "execute trade",
        "buy stock",
        "sell stock",
        "transfer money",
        "wire money",
        "rotate secret",
        "change password",
        "部署到生产",
        "生产环境部署",
        "删除数据库",
        "删除生产",
        "对外发送",
        "发送邮件",
        "发送消息",
        "公开发布",
        "执行交易",
        "股票下单",
        "买入股票",
        "卖出股票",
        "转账",
        "汇款",
        "修改密码",
        "轮换密钥",
    )

    def evaluate(self, goal: str) -> ApprovalDecision:
        normalized = " ".join(goal.lower().split())
        for phrase in self._HIGH_IMPACT_PHRASES:
            if phrase in normalized:
                return ApprovalDecision(
                    required=True,
                    reason=f"High-impact action matched approval rule: {phrase}",
                )
        return ApprovalDecision(required=False)
