from typing import List


class Logger:
    """
    A simple logger that stores messages in memory.
    """
    def __init__(self) -> None:
        self._messages: List[str] = []

    def log(self, message: str) -> None:
        self._messages.append(message)

    def messages(self) -> List[str]:
        """
        Return all logged messages in order.
        """
        result: List[str] = []
        for m in self._messages:
            result.append(m)
        return result


class Service:
    """
    A service that processes integers and logs what it is doing.
    This class demonstrates composition: Service has a Logger.
    """
    def __init__(self, name: str, factor: int, logger: Logger) -> None:
        self.name = name
        self.factor = factor
        self.logger = logger

    def handle(self, data: int) -> int:
        """
        Multiply data by factor, log the operation, and return the result.
        Example log message format (exact format not required, but must contain key
        info):
        "svc=alpha data=10 factor=3 result=30"
        """
        result = data * self.factor
        self.logger.log(
            f"svc={self.name} data={data} factor={self.factor} result={result}"
        )
        return result

    def __str__(self) -> str:
        """
        Return a readable string representation, e.g.:
        "Service(name=alpha, factor=3)"
        """
        return f"Service(name={self.name}, factor={self.factor})"
