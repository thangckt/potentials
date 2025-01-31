# coding: utf-8
# Standard Python libraries
import io
from typing import Optional, Tuple, Union

# https://github.com/usnistgov/DataModelDict
from DataModelDict import DataModelDict as DM

# https://github.com/usnistgov/yabadaba
from yabadaba.record import Record
from yabadaba import load_query 

# https://pandas.pydata.org/
import pandas as pd

__all__ = ['FAQ']

class FAQ(Record):
    """
    Class for representing FAQ records that document the FAQs for the NIST
    Interatomic Potentials Repository.
    """
    def __init__(self,
                 model: Union[str, io.IOBase, DM, None] = None,
                 name: Optional[str] = None,
                 **kwargs):
        """
        Initializes a Record object for a given style.
        
        Parameters
        ----------
        model : str, file-like object or DataModelDict, optional
            A JSON/XML data model for the content.
        name : str, optional
            The unique name to assign to the record.  If model is a file
            path, then the default record name is the file name without
            extension.
        """
        self.__question = None
        self.__answer = None
        super().__init__(model=model, name=name, **kwargs)

    @property
    def style(self) -> str:
        """str: The record style"""
        return 'FAQ'

    @property
    def modelroot(self) -> str:
        """str: The root element of the content"""
        return 'faq'
    
    @property
    def xsl_filename(self) -> Tuple[str, str]:
        """tuple: The module path and file name of the record's xsl html transformer"""
        return ('potentials.xsl', 'FAQ.xsl')

    @property
    def xsd_filename(self) -> Tuple[str, str]:
        """tuple: The module path and file name of the record's xsd schema"""
        return ('potentials.xsd', 'FAQ.xsd')

    @property
    def question(self) -> Optional[str]:
        """str: The frequently asked question."""
        return self.__question

    @question.setter
    def question(self, value: Optional[str]):
        if value is None:
            self.__question = None
        else:
            self.__question = str(value)

    @property
    def answer(self) -> Optional[str]:
        """str: The answer to the frequently asked question."""
        return self.__answer

    @answer.setter
    def answer(self, value: Optional[str]):
        if value is None:
            self.__answer = None
        else:
            self.__answer = str(value)

    def load_model(self,
                   model: Union[str, io.IOBase, DM],
                   name: Optional[str] = None):
        """
        Loads record contents from a given model.

        Parameters
        ----------
        model : str, file-like object or DataModelDict
            A JSON/XML data model for the content.
        name : str, optional
            The name to assign to the record.  Often inferred from other
            attributes if not given.
        """
        super().load_model(model, name=name)

        faq = self.model[self.modelroot]
        self.question = faq['question']
        self.answer = faq['answer']

    def set_values(self,
                   name: Optional[str] = None,
                   question: Optional[str] = None,
                   answer: Optional[str] = None):
        """
        Set multiple object attributes at the same time.

        Parameters
        ----------
        name : str, optional
            The name to assign to the record.  Often inferred from other
            attributes if not given.
        question : str, optional
            The frequently asked question.
        answer : str, optional
            The answer to the frequently asked question.
        """
        if question is not None:
            self.question = question
        if answer is not None:
            self.answer = answer
        if name is not None:
            self.name = name

    def build_model(self) -> DM:
        """
        Generates and returns model content based on the values set to object.
        """
        model = DM()
        model['faq'] = DM()
        model['faq']['question'] = self.question
        model['faq']['answer'] = self.answer

        self._set_model(model)
        return model

    def metadata(self) -> dict:
        """
        Generates a dict of simple metadata values associated with the record.
        Useful for quickly comparing records and for building pandas.DataFrames
        for multiple records of the same style.
        """
        meta = {}
        meta['name'] = self.name
        meta['question'] = self.question
        meta['answer'] = self.answer
        return meta

    @property
    def queries(self) -> dict:
        """dict: Query objects and their associated parameter names."""
        return {
            'question': load_query(
                style='str_contains',
                name='question',
                path=f'{self.modelroot}.question'),
            'answer': load_query(
                style='str_contains',
                name='answer',
                path=f'{self.modelroot}.answer'),
        }

    def pandasfilter(self,
                     dataframe: pd.DataFrame,
                     name: Union[str, list, None] = None,
                     question: Union[str, list, None] = None,
                     answer: Union[str, list, None] = None) -> pd.Series:
        """
        Filters a pandas.DataFrame based on kwargs values for the record style.
        
        Parameters
        ----------
        dataframe : pandas.DataFrame
            A table of metadata for multiple records of the record style.
        name : str or list
            The record name(s) to parse by.
        question : str or list
            Term(s) to search for in the question field.
        answer : str or list
            Term(s) to search for in the answer field.
        
        Returns
        -------
        pandas.Series, numpy.NDArray
            Boolean map of matching values
        """
        matches = super().pandasfilter(dataframe, name=name, question=question,
                                       answer=answer)
        return matches

    def mongoquery(self,
                   name: Union[str, list, None] = None,
                   question: Union[str, list, None] = None,
                   answer: Union[str, list, None] = None) -> dict:
        """
        Builds a Mongo-style query based on kwargs values for the record style.
        
        Parameters
        ----------
        name : str or list
            The record name(s) to parse by.
        question : str or list
            Term(s) to search for in the question field.
        answer : str or list
            Term(s) to search for in the answer field.
        
        Returns
        -------
        dict
            The Mongo-style query
        """     
        mquery = super().mongoquery(name=name, question=question, answer=answer)
        return mquery

    def cdcsquery(self,
                  question: Union[str, list, None] = None,
                  answer: Union[str, list, None] = None) -> dict:
        """
        Builds a CDCS-style query based on kwargs values for the record style.
        
        Parameters
        ----------
        question : str or list
            Term(s) to search for in the question field.
        answer : str or list
            Term(s) to search for in the answer field.
        
        Returns
        -------
        dict
            The CDCS-style query
        """
        mquery = super().cdcsquery(question=question, answer=answer)
        return mquery