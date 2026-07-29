import { create } from 'zustand';
import type { Book } from '../types';

interface BookState {
  books: Book[];
  selectedBookIds: string[];
  isUploadModalOpen: boolean;
  setBooks: (books: Book[]) => void;
  addBook: (book: Book) => void;
  removeBook: (bookId: string) => void;
  toggleBookSelection: (bookId: string) => void;
  clearSelectedBooks: () => void;
  openUploadModal: () => void;
  closeUploadModal: () => void;
}

export const useBookStore = create<BookState>((set) => ({
  books: [],
  selectedBookIds: [],
  isUploadModalOpen: false,

  setBooks: (books) => set({ books }),
  addBook: (book) => set((state) => ({ books: [book, ...state.books] })),
  removeBook: (bookId) =>
    set((state) => ({
      books: state.books.filter((b) => b.id !== bookId),
      selectedBookIds: state.selectedBookIds.filter((id) => id !== bookId),
    })),

  toggleBookSelection: (bookId) =>
    set((state) => {
      const exists = state.selectedBookIds.includes(bookId);
      if (exists) {
        return { selectedBookIds: state.selectedBookIds.filter((id) => id !== bookId) };
      } else {
        return { selectedBookIds: [...state.selectedBookIds, bookId] };
      }
    }),

  clearSelectedBooks: () => set({ selectedBookIds: [] }),
  openUploadModal: () => set({ isUploadModalOpen: true }),
  closeUploadModal: () => set({ isUploadModalOpen: false }),
}));
