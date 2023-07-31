from pydantic import BaseModel
from typing import Generic, Optional, TypeVar

T = TypeVar('T')

class DefualtResponseModel(BaseModel, Generic[T]):
    data: Optional[T] = None

class Node:
      def __init__(self, data):
         self.left = None
         self.right = None
         self.data = data

      def insert(self, data):
         if self.data:
            if data < self.data:
               if self.left is None:
                  self.left = Node(data)
               else:
                  self.left.insert(data)
            elif data > self.data:
                  if self.right is None:
                     self.right = Node(data)
                  else:
                     self.right.insert(data)
         else:
            self.data = data
      