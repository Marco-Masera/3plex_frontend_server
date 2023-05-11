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
            