from triplex_frontend.responses import Responses
from rest_framework import status

class TriplexException(Exception):
    def handle(self):
        return Responses.generic_failure()

class ModuleNotImplementedYetException(TriplexException):
    def handle(self):
        return Responses.generic_failure(message="The module is not ready yet")

class SsRnaNotProvidedException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="You need to provide either a ssRNA fasta file as 'SSRNA_FASTA' or an Id as 'SSRNA_ID'",
            errorCode= status.HTTP_400_BAD_REQUEST)

class DsDnaNotProvidedException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="You need to provide either a dsDNA fasta file as 'DSDNA_FASTA' or a bed file as 'DSDNA_COORD_BED'",
            errorCode= status.HTTP_400_BAD_REQUEST)

class CannotSubmitToBackendException(TriplexException):
    def handle(self):
        return Responses.generic_failure(message="Cannot submit job right now - backend server unavailable.")

class DataDoesNotExistException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="The requested data does not exist in the system",
            errorCode= status.HTTP_404_NOT_FOUND)

class TokenDoesNotExistException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="The requested token does not exist in the system",
            errorCode= status.HTTP_404_NOT_FOUND)

class DidNotReceiveInputFilesException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="Did not receive expected input files",
            errorCode= status.HTTP_400_BAD_REQUEST)

class TokenIsNotStateSubmittedException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="The requested token is in the system but not in state Submitted; cannot accept incoming data")
            
class DataNotReadyYetException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="Job is not completed yet",
            errorCode= status.HTTP_307_TEMPORARY_REDIRECT)
class DataExpiredException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="Job data expired and is not available anymore",
            errorCode= status.HTTP_410_GONE)
            
class JobCancelledException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="Job was cancelled",
            errorCode= status.HTTP_410_GONE)
class JobFailedException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="Job failed",
            errorCode= status.HTTP_410_GONE)

class TriplexParamOutOfBound(TriplexException):
    def __init__(self, message):
        self.message = message 
        super().__init__(self)
    def handle(self):
        return Responses.generic_failure(
            message=self.message,
            errorCode= status.HTTP_400_BAD_REQUEST)

class Unauthorized(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="Qualcuno sta provando a fare il furbetto??",
            errorCode= status.HTTP_401_UNAUTHORIZED)

class InputFileTooBig(TriplexException):
    def __init__(self, message):
        self.message = message 
        super().__init__(self)
    def handle(self):
        return Responses.generic_failure(
            message=self.message,
            errorCode= status.HTTP_400_BAD_REQUEST)