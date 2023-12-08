from triplex_frontend.responses import Responses
from rest_framework import status
from rest_framework.response import Response

class TriplexException(Exception):
    def handle(self):
        return Responses.generic_failure()

class ModuleNotImplementedYetException(TriplexException):
    def handle(self):
        return Responses.generic_failure(message="The module is not ready yet on the server side")

class SsRnaNotProvidedException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="You need to provide either a ssRNA fasta file as 'SSRNA_FASTA' or an Id as 'SSRNA_ID'",
            errorCode= status.HTTP_400_BAD_REQUEST)

class SsRnaIdNotValidException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="The longest transcript id provided is not recognized in the system.",
            errorCode= status.HTTP_400_BAD_REQUEST)

class DsDnaNotProvidedException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="You need to provide either a dsDNA fasta file as 'DSDNA_FASTA' or a bed file as 'DSDNA_COORD_BED'",
            errorCode= status.HTTP_400_BAD_REQUEST)

class SpeciesNotProvidedException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="You need to provide a species for the job",
            errorCode= status.HTTP_400_BAD_REQUEST)
class SpeciesNotSupportedException(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="The provided species is not supported.",
            errorCode= status.HTTP_400_BAD_REQUEST)

class NumIterationsNotAllowed(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="The provided number of iterations is not allowed.",
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

class TPXNotFound(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="No tpx found",
            errorCode= status.HTTP_404_NOT_FOUND)

class BackgroundGenesNotIncludedInPutative(TriplexException):
    def handle(self):
        return Responses.generic_failure(
            message="Background genes are not included in putative genes",
            errorCode= status.HTTP_400_BAD_REQUEST)
class BackgroundGenesNotIncludedInMANE(TriplexException):
    def __init__(self, genes):
        self.genes = genes 
        super().__init__(self)
    def handle(self): #notIncludedInMANE
        return Responses.personalized_failure(
            {"notIncludedInMANE": self.genes},
            errorCode= status.HTTP_400_BAD_REQUEST)