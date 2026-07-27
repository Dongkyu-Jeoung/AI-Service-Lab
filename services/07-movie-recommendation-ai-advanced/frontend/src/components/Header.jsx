// components/Header.jsx
// 서비스 제목 + 부제 + 모델 미준비 경고

export default function Header({ modelLoaded }) {
  return (
    <header className="page-header">
      <p className="badge">AI Service Blueprint</p>
      <h1>Movie Recommendation AI Advanced</h1>
      <p className="subtitle">사용자 평점 이력을 분석하여 취향에 맞는 영화를 추천합니다.</p>
      {!modelLoaded && (
        <p className="model-warning">
          아직 학습된 추천 모델이 없습니다. data 폴더에 MovieLens 100K 데이터를 추가한 뒤
          모델을 학습하면 추천 기능을 사용할 수 있습니다.
        </p>
      )}
    </header>
  );
}
