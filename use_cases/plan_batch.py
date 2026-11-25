"""História 7: conferir o resumo da operação antes de confirmar."""
from domain.batch import BatchProgress
from use_cases.batch_request import BatchRequest
from use_cases.batch_view import BatchView


class PlanBatch:
    def execute(self, user_id: int, request: BatchRequest) -> BatchView:
        """Valida e calcula os nomes finais; não grava nada."""
        batch, items = request.build(user_id)
        return BatchView(batch, BatchProgress(total=len(items)), items)
